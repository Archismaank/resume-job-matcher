# app/agents/recommender.py

import asyncio
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
from app.parsers.adzuna_client import search_adzuna_jobs
from app.parsers.jsearch_client import search_jsearch_jobs
from app.parsers.naukri_scraper import search_naukri_jobs

# Thread pool for running sync OpenAI calls in parallel
_executor = ThreadPoolExecutor(max_workers=5)


async def generate_search_query(resume: ResumeData) -> str:
    """
    Uses OpenAI to generate the best job search query
    from the candidate's resume.
    """
    from openai import OpenAI

    client = OpenAI(api_key=settings.openai_api_key)

    prompt = SEARCH_QUERY_PROMPT.format(
        skills=", ".join(resume.skills[:15]),
        experience_years=resume.total_experience_years,
        recent_role=resume.experience[0].role if resume.experience else "",
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You generate job search queries. Return only the query string."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0,
        max_tokens=50,
    )

    query = response.choices[0].message.content.strip()
    query = query.strip('"').strip("'")

    return query


async def fetch_all_jobs(
    query: str,
    preferences: SearchPreferences,
) -> list[JobListing]:
    """
    Searches all three sources in parallel.
    Returns combined list of JobListing objects.
    """

    # Run Adzuna and JSearch in parallel
    adzuna_jobs, jsearch_jobs = await asyncio.gather(
        search_adzuna_jobs(
            query=query,
            location=preferences.location,
            remote_only=preferences.remote_only,
            results_per_page=5,
        ),
        search_jsearch_jobs(
            query=query,
            location=preferences.location,
            employment_type=preferences.employment_type,
            remote_only=preferences.remote_only,
            num_pages=1,
        ),
    )

    # Naukri uses sync playwright — run in thread pool
    loop = asyncio.get_event_loop()
    naukri_jobs = await loop.run_in_executor(
        None,
        lambda: search_naukri_jobs(
            query=query,
            location=preferences.location,
            remote_only=preferences.remote_only,
            employment_type=preferences.employment_type,
        )
    )

    print(f"Adzuna: {len(adzuna_jobs)} jobs")
    print(f"JSearch: {len(jsearch_jobs)} jobs")
    print(f"Naukri: {len(naukri_jobs)} jobs")

    all_jobs = adzuna_jobs + jsearch_jobs + naukri_jobs
    return all_jobs


def deduplicate_jobs(jobs: list[JobListing]) -> list[JobListing]:
    """
    Removes duplicate job listings based on title + company.
    """
    seen = set()
    unique_jobs = []

    for job in jobs:
        key = f"{job.title.lower()}_{job.company.lower()}"
        if key not in seen:
            seen.add(key)
            unique_jobs.append(job)

    return unique_jobs


def convert_listing_to_job_data(listing: JobListing):
    """
    Converts a JobListing to JobData for analysis.
    """
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
    Analyzes a single job against resume synchronously.
    Designed to run in a thread pool.
    """
    try:
        job_data = convert_listing_to_job_data(job_listing)

        # If no skills extract from description using OpenAI
        if not job_data.required_skills and job_listing.description:
            job_data = extract_job_data(job_listing.description)
            job_data.title = job_listing.title
            job_data.company = job_listing.company

        # Skip if still no useful data
        if not job_data.required_skills and not job_data.description:
            print(f"  Skipping {job_listing.title} — no skills or description")
            return None

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
        print(f"  Failed to analyze {job_listing.title}: {e}")
        return None


async def _analyze_all_jobs_parallel(
    resume: ResumeData,
    jobs: list[JobListing],
) -> list[JobRecommendation]:
    """
    Analyzes all jobs in parallel using a thread pool.
    Each job analysis runs in its own thread — all run simultaneously.
    """
    loop = asyncio.get_event_loop()

    # Create one future per job — all submitted at once
    futures = [
        loop.run_in_executor(
            _executor,
            _analyze_single_job_sync,
            resume,
            job,
        )
        for job in jobs
    ]

    print(f"Analyzing {len(futures)} jobs in parallel...")

    # Wait for all analyses to complete
    results = await asyncio.gather(*futures, return_exceptions=True)

    # Filter out None and exceptions
    recommendations = []
    for result in results:
        if isinstance(result, Exception):
            print(f"  Analysis exception: {result}")
        elif result is not None:
            recommendations.append(result)

    return recommendations


async def generate_recommendations(
    resume: ResumeData,
    preferences: SearchPreferences,
    top_n: int = 10,
) -> tuple[list[JobRecommendation], str]:
    """
    Main orchestrator for the recommendation pipeline.

    Steps:
    1. Generate search query from resume
    2. Fetch jobs from each portal in parallel
    3. Deduplicate
    4. Analyze ALL jobs in parallel using thread pool
    5. Sort by match percentage
    6. Return top N with ranks
    """

    # Step 1 — generate search query
    search_query = await generate_search_query(resume)
    print(f"Search query: {search_query}")

    # Step 2 — fetch from all portals in parallel
    all_jobs = await fetch_all_jobs(search_query, preferences)
    print(f"Total jobs fetched: {len(all_jobs)}")

    # Step 3 — deduplicate
    unique_jobs = deduplicate_jobs(all_jobs)
    print(f"After deduplication: {len(unique_jobs)} jobs")

    # Step 4 — analyze ALL jobs in parallel
    recommendations = await _analyze_all_jobs_parallel(resume, unique_jobs)
    print(f"Successfully analyzed: {len(recommendations)} jobs")

    # Step 5 — sort by match percentage highest first
    recommendations.sort(
        key=lambda r: r.match_percentage,
        reverse=True
    )

    # Step 6 — take top N and assign ranks
    top_recommendations = recommendations[:top_n]
    for i, rec in enumerate(top_recommendations):
        rec.rank = i + 1

    return top_recommendations, search_query