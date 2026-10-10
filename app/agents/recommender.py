# app/agents/recommender.py

import json
import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from app.config import settings
from app.models.schemas import (
    ResumeData,
    JobListing,
    JobRecommendation,
    SearchPreferences,
)
from app.agents.analyzer import extract_job_data, analyze_resume_against_job
from app.agents.scorer import get_match_label, get_match_color
from app.agents.prompts import SEARCH_QUERY_PROMPT
from app.rag.embedder import embed_text, embed_batch, build_resume_embed_text
from app.rag.similarity import cosine_similarity
from app.parsers.adzuna_client import search_adzuna_jobs
from app.parsers.jsearch_client import search_jsearch_jobs
from app.parsers.naukri_scraper import search_naukri_jobs

logger = logging.getLogger(__name__)

# Thread pool for running sync OpenAI / Playwright calls in parallel
_executor = ThreadPoolExecutor(max_workers=8)


# ─── Query Generation ──────────────────────────────────────────────────────────

def _extract_domain_keywords(resume: ResumeData) -> str:
    """
    Extracts domain/industry keywords from resume experience descriptions.
    Used to inform the domain_query generation.
    """
    domain_hints = []

    # Pull company names and role descriptions for domain signals
    for exp in resume.experience:
        if exp.company:
            domain_hints.append(exp.company)
        if exp.description:
            # Take first 80 chars of description as domain signal
            domain_hints.append(exp.description[:80])

    # Also include project names as domain signals
    for proj in resume.projects:
        if proj.name:
            domain_hints.append(proj.name)

    return ", ".join(domain_hints[:6]) if domain_hints else "general software"


async def generate_search_queries(resume: ResumeData) -> list[str]:
    """
    Generates THREE complementary job search queries using a richer resume context.

    The 3 queries target different angles:
      - role_query:   seniority + role title (e.g. "Senior Python Backend Engineer")
      - tech_query:   key tech stack + role type (e.g. "FastAPI Microservices Developer")
      - domain_query: domain/industry + role (e.g. "Backend Engineer FinTech")

    Together they give 3× more diverse job results from portals,
    which RAG pre-ranking then filters down to the most relevant.

    Returns:
        List of 3 unique query strings (deduped). Falls back to [role_query] on parse error.
    """
    from openai import OpenAI
    client = OpenAI(api_key=settings.openai_api_key)

    # ── Build richer context for the prompt ──────────────────────────────────
    recent_role = resume.experience[0].role if resume.experience else "Software Engineer"

    # All role titles newest first
    all_roles = ", ".join(
        [f"{e.role} at {e.company}" for e in resume.experience]
    ) if resume.experience else recent_role

    # Categorise skills: top 10 most specific technical ones first
    top_skills = ", ".join(resume.skills[:12]) if resume.skills else ""

    # Domain keywords from experience descriptions + project names
    domain_keywords = _extract_domain_keywords(resume)

    # Key projects with tech stack
    top_projects = ", ".join(
        [f"{p.name} ({', '.join(p.tech_stack[:3])})" for p in resume.projects[:3]]
    ) if resume.projects else "N/A"

    certifications = ", ".join(resume.certifications[:4]) if resume.certifications else "N/A"

    prompt = SEARCH_QUERY_PROMPT.format(
        recent_role=recent_role,
        all_roles=all_roles,
        experience_years=resume.total_experience_years,
        top_skills=top_skills,
        domain_keywords=domain_keywords,
        top_projects=top_projects,
        certifications=certifications,
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert technical recruiter. "
                    "Always respond with valid JSON only — no markdown, no explanation."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.1,   # Slight creativity for query diversity
        max_tokens=120,
        seed=42,
    )

    raw = response.choices[0].message.content.strip()

    # ── Parse the 3-query JSON response ──────────────────────────────────────
    try:
        # Strip markdown code blocks if GPT wraps in them
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        data = json.loads(raw)
        queries = [
            data.get("role_query", "").strip(),
            data.get("tech_query", "").strip(),
            data.get("domain_query", "").strip(),
        ]

        # Filter empty strings and deduplicate while preserving order
        seen = set()
        unique_queries = []
        for q in queries:
            if q and q.lower() not in seen:
                seen.add(q.lower())
                unique_queries.append(q)

        if not unique_queries:
            raise ValueError("All queries were empty")

        logger.info(f"[query-gen] Generated {len(unique_queries)} queries: {unique_queries}")
        return unique_queries

    except Exception as e:
        # Graceful fallback: extract any plain text as a single query
        logger.warning(f"[query-gen] Failed to parse multi-query JSON: {e}. Raw: {raw!r}")
        fallback = raw.strip().strip('"').strip("'")
        fallback = fallback if fallback else f"{recent_role}"
        logger.info(f"[query-gen] Falling back to single query: {fallback!r}")
        return [fallback]


# ─── Job Fetching — Multi-Query Fan-Out ────────────────────────────────────────

async def fetch_all_jobs_multi_query(
    queries: list[str],
    preferences: SearchPreferences,
) -> list[JobListing]:
    """
    Fetches jobs from all portals for ALL queries simultaneously.

    Pattern: Q queries × 3 portals = up to 9 concurrent API calls
    (e.g. 3 queries × Adzuna + JSearch + Naukri = 9 calls, all in parallel)

    This gives 3× the job diversity compared to a single query,
    while not adding any latency because all calls fire at the same time.

    Returns:
        Combined list of JobListing from all queries and portals (before dedup).
    """
    all_jobs: list[JobListing] = []

    # ── Async portals: Adzuna + JSearch for all queries in one gather ─────────
    async_tasks = []
    for query in queries:
        async_tasks.append(
            search_adzuna_jobs(
                query=query,
                location=preferences.location,
                remote_only=preferences.remote_only,
                results_per_page=5,
            )
        )
        async_tasks.append(
            search_jsearch_jobs(
                query=query,
                location=preferences.location,
                employment_type=preferences.employment_type,
                remote_only=preferences.remote_only,
                num_pages=1,
            )
        )

    # All async portal calls fire simultaneously
    async_results = await asyncio.gather(*async_tasks, return_exceptions=True)

    for i, result in enumerate(async_results):
        portal = "Adzuna" if i % 2 == 0 else "JSearch"
        query_idx = i // 2
        if isinstance(result, Exception):
            logger.warning(f"[fetch] {portal} failed for query[{query_idx}] '{queries[query_idx]}': {result}")
        elif isinstance(result, list):
            logger.info(f"[fetch] {portal} query[{query_idx}] '{queries[query_idx]}': {len(result)} jobs")
            all_jobs.extend(result)

    # ── Sync portal: Naukri — run all queries in thread pool simultaneously ───
    loop = asyncio.get_event_loop()
    naukri_futures = [
        loop.run_in_executor(
            _executor,
            lambda q=query: search_naukri_jobs(
                query=q,
                location=preferences.location,
                remote_only=preferences.remote_only,
                employment_type=preferences.employment_type,
            )
        )
        for query in queries
    ]
    naukri_results = await asyncio.gather(*naukri_futures, return_exceptions=True)

    for i, result in enumerate(naukri_results):
        if isinstance(result, Exception):
            logger.warning(f"[fetch] Naukri failed for query[{i}] '{queries[i]}': {result}")
        elif isinstance(result, list):
            logger.info(f"[fetch] Naukri query[{i}] '{queries[i]}': {len(result)} jobs")
            all_jobs.extend(result)

    return all_jobs


# ─── Deduplication ─────────────────────────────────────────────────────────────

def deduplicate_jobs(jobs: list[JobListing]) -> list[JobListing]:
    """
    Removes duplicate job listings based on normalised title + company.
    With multi-query, the same job may appear from different queries — this cleans that up.
    """
    seen = set()
    unique_jobs = []

    for job in jobs:
        key = f"{job.title.lower().strip()}_{job.company.lower().strip()}"
        if key not in seen:
            seen.add(key)
            unique_jobs.append(job)

    return unique_jobs


# ─── RAG Pre-ranking ───────────────────────────────────────────────────────────

def pre_rank_jobs_by_semantic_similarity(
    resume: ResumeData,
    jobs: list[JobListing],
    top_n: int = 15,
) -> list[tuple[JobListing, float]]:
    """
    RAG-based pre-ranking: embeds the resume and all job descriptions in ONE batch
    API call, then ranks by cosine similarity. No GPT analysis yet — pure math.

    With multi-query fan-out, the job pool is now ~45 jobs.
    This pre-ranking filters to the top 15 most semantically relevant
    before sending to GPT analysis — keeping costs low.

    Args:
        resume: Structured resume data
        jobs:   All deduplicated job listings from all portals and queries
        top_n:  How many top candidates to return for full GPT analysis

    Returns:
        List of (JobListing, semantic_score) tuples, sorted by similarity descending.
    """
    if not jobs:
        return []

    logger.info(f"[RAG pre-rank] Embedding resume + {len(jobs)} jobs in one batch call...")

    resume_text = build_resume_embed_text(resume)

    # Build embedding text for each job
    job_texts = []
    for job in jobs:
        parts = []
        if job.title:
            parts.append(f"Role: {job.title}")
        if job.required_skills:
            parts.append("Required: " + ", ".join(job.required_skills))
        if job.preferred_skills:
            parts.append("Preferred: " + ", ".join(job.preferred_skills))
        if job.description:
            parts.append(job.description[:1000])
        job_texts.append(" | ".join(parts) or job.title or "unknown job")

    try:
        resume_vec = embed_text(resume_text)
        job_vecs = embed_batch(job_texts)
    except Exception as e:
        logger.warning(f"[RAG pre-rank] Embedding failed, skipping pre-ranking: {e}")
        return [(job, 50.0) for job in jobs[:top_n]]

    # Cosine similarity for each job
    scored = [
        (job, round(cosine_similarity(resume_vec, job_vec) * 100, 2))
        for job, job_vec in zip(jobs, job_vecs)
    ]
    scored.sort(key=lambda x: x[1], reverse=True)

    top = scored[:top_n]
    logger.info(
        f"[RAG pre-rank] Top {len(top)} by semantic similarity: "
        + ", ".join(f"{j.title}({s:.1f}%)" for j, s in top[:5])
    )
    return top


# ─── Single Job Analysis ───────────────────────────────────────────────────────

def convert_listing_to_job_data(listing: JobListing):
    """Converts a JobListing to JobData for analysis."""
    from app.models.schemas import JobData
    return JobData(
        title=listing.title,
        company=listing.company,
        required_skills=listing.required_skills,
        preferred_skills=listing.preferred_skills,
        experience_required=listing.experience_required,
        education_required=listing.education_required,
        description=listing.description,
    )


def _analyze_single_job_sync(
    resume: ResumeData,
    job_listing: JobListing,
) -> JobRecommendation | None:
    """
    Analyzes a single job against the resume synchronously.
    Runs in a thread pool so all jobs are analyzed in parallel.
    analyze_resume_against_job() internally runs RAG semantic scoring + GPT analysis.
    """
    try:
        job_data = convert_listing_to_job_data(job_listing)

        # If no structured skills, extract from description using OpenAI
        if not job_data.required_skills and job_listing.description:
            job_data = extract_job_data(job_listing.description)
            job_data.title = job_listing.title
            job_data.company = job_listing.company

        # Skip if still no useful data
        if not job_data.required_skills and not job_data.description:
            logger.debug(f"Skipping '{job_listing.title}' — no skills or description")
            return None

        # Full analysis: RAG semantic + GPT structured + blended score
        analysis = analyze_resume_against_job(resume, job_data)

        return JobRecommendation(
            rank=0,
            match_percentage=analysis.match_percentage,
            match_label=get_match_label(analysis.match_percentage),
            match_color=get_match_color(analysis.match_percentage),
            job=job_listing,
            matched_skills=analysis.matched_skills,
            missing_skills=analysis.missing_skills,
            bonus_skills=analysis.bonus_skills,
            summary=analysis.summary,
        )

    except Exception as e:
        logger.warning(f"Failed to analyze '{job_listing.title}': {e}")
        return None


async def _analyze_all_jobs_parallel(
    resume: ResumeData,
    jobs: list[JobListing],
) -> list[JobRecommendation]:
    """Analyzes all jobs in parallel using a thread pool."""
    loop = asyncio.get_event_loop()

    futures = [
        loop.run_in_executor(_executor, _analyze_single_job_sync, resume, job)
        for job in jobs
    ]

    logger.info(f"Analyzing {len(futures)} pre-ranked jobs in parallel (RAG + GPT)...")
    results = await asyncio.gather(*futures, return_exceptions=True)

    recommendations = []
    for result in results:
        if isinstance(result, Exception):
            logger.warning(f"Analysis exception: {result}")
        elif result is not None:
            recommendations.append(result)

    return recommendations


# ─── Main Pipeline ─────────────────────────────────────────────────────────────

async def generate_recommendations(
    resume: ResumeData,
    preferences: SearchPreferences,
    top_n: int = 10,
) -> tuple[list[JobRecommendation], str]:
    """
    Main recommendation pipeline (fully upgraded with multi-query + RAG).

    Steps:
    1. Generate 3 complementary search queries (role, tech, domain) — 1 GPT call
    2. Fetch jobs from all portals for ALL 3 queries simultaneously (up to 9 parallel calls)
    3. Deduplicate (~45 raw → ~25 unique)
    4. RAG pre-rank: embed resume + all jobs in one batch → cosine similarity → top 15
    5. Full GPT + semantic analysis on top 15 only (parallel thread pool)
    6. Sort by final blended score → return top N with ranks

    Cost vs old pipeline:
    - Query gen:    1 GPT call (same)
    - Fetching:     3× more jobs but same latency (all parallel)
    - RAG pre-rank: 1 batch embed call (new, very cheap ~$0.000003)
    - GPT analysis: ~15 calls (down from ~40, 62% reduction)
    """

    # Step 1 — Generate 3 complementary search queries
    queries = await generate_search_queries(resume)
    logger.info(f"[pipeline] Queries: {queries}")

    # Flatten to one string for storage/display (the primary role query)
    primary_query = queries[0]

    # Step 2 — Fetch jobs for ALL queries from ALL portals simultaneously
    all_jobs = await fetch_all_jobs_multi_query(queries, preferences)
    logger.info(f"[pipeline] Total raw jobs fetched: {len(all_jobs)}")

    # Step 3 — Deduplicate
    unique_jobs = deduplicate_jobs(all_jobs)
    logger.info(f"[pipeline] After dedup: {len(unique_jobs)} unique jobs")

    if not unique_jobs:
        return [], primary_query

    # Step 4 — RAG pre-rank by semantic similarity (one batch embed call)
    pre_ranked = pre_rank_jobs_by_semantic_similarity(resume, unique_jobs, top_n=15)
    top_candidates = [job for job, _score in pre_ranked]
    logger.info(f"[pipeline] RAG pre-ranked to top {len(top_candidates)} for GPT analysis")

    # Step 5 — Full GPT + semantic analysis on top candidates in parallel
    recommendations = await _analyze_all_jobs_parallel(resume, top_candidates)
    logger.info(f"[pipeline] Successfully analyzed: {len(recommendations)} jobs")

    # Step 6 — Sort by blended score, take top N, assign ranks
    recommendations.sort(key=lambda r: r.match_percentage, reverse=True)
    top_recommendations = recommendations[:top_n]
    for i, rec in enumerate(top_recommendations):
        rec.rank = i + 1

    return top_recommendations, primary_query