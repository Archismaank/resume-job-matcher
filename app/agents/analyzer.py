# app/agents/analyzer.py

import json
import logging
from openai import OpenAI
from app.config import settings
from app.models.schemas import ResumeData, JobData, AnalysisResult, SkillGap
from app.agents.prompts import RESUME_EXTRACTION_PROMPT, JOB_EXTRACTION_PROMPT, ANALYSIS_PROMPT
from app.agents.scorer import calculate_match_percentage
from app.rag.embedder import embed_text, build_resume_embed_text, build_job_embed_text
from app.rag.similarity import cosine_similarity, cosine_similarity_to_percentage

logger = logging.getLogger(__name__)

# Reuse one OpenAI client across all calls
client = OpenAI(api_key=settings.openai_api_key)


def clean_json_response(raw_response: str) -> str:
    """
    Cleans OpenAI response and extracts pure JSON from it.
    Finds the first { and last } and extracts everything between them.
    This is the most reliable approach regardless of markdown formatting.
    """
    cleaned = raw_response.strip()

    # Find the first { and last } in the response
    # Everything between them is our JSON
    start = cleaned.find("{")
    end = cleaned.rfind("}")

    if start == -1 or end == -1:
        raise ValueError(f"No valid JSON found in response: {cleaned}")

    # Extract just the JSON part
    cleaned = cleaned[start:end + 1]

    return cleaned


def extract_resume_data(raw_text: str) -> ResumeData:
    """
    Takes raw resume text and sends it to OpenAI.
    OpenAI extracts the structured data and returns JSON.
    We validate that JSON with Pydantic and return a ResumeData object.
    """
    prompt = RESUME_EXTRACTION_PROMPT.format(resume_text=raw_text)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You are an expert resume parser. Always respond with valid JSON only."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0,
        max_tokens=2000,
        seed=42,
    )

    raw_response = response.choices[0].message.content.strip()
    clean_response = clean_json_response(raw_response)
    data = json.loads(clean_response)

    if not isinstance(data, dict):
        raise ValueError(
            f"Resume extraction failed: AI returned '{type(data).__name__}' instead of a JSON object."
        )

    # Sanitize: AI sometimes returns null for list/numeric fields — apply safe defaults
    for list_field in ("skills", "experience", "projects", "education", "certifications"):
        if not isinstance(data.get(list_field), list):
            data[list_field] = []
    if not isinstance(data.get("total_experience_years"), (int, float)):
        data["total_experience_years"] = 0.0

    resume_data = ResumeData(**data)
    return resume_data


def extract_job_data(raw_text: str) -> JobData:
    """
    Takes raw job posting text and sends it to OpenAI.
    OpenAI extracts the structured data and returns JSON.
    We validate that JSON with Pydantic and return a JobData object.
    """
    prompt = JOB_EXTRACTION_PROMPT.format(job_text=raw_text)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You are an expert job posting parser. Always respond with valid JSON only."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0,
        max_tokens=4000,
        seed=42,
    )

    raw_response = response.choices[0].message.content.strip()
    clean_response = clean_json_response(raw_response)
    data = json.loads(clean_response)

    if not isinstance(data, dict):
        raise ValueError(
            f"Job extraction failed: AI returned '{type(data).__name__}' instead of a JSON object. "
            "The page content may not contain a valid job description."
        )

    # Sanitize: AI sometimes returns null for list fields — convert to empty lists
    for list_field in ("required_skills", "preferred_skills"):
        if not isinstance(data.get(list_field), list):
            data[list_field] = []
    for str_field in ("title", "company", "experience_required", "education_required", "description"):
        if not isinstance(data.get(str_field), str):
            data[str_field] = ""

    job_data = JobData(**data)
    return job_data


def compute_semantic_similarity(resume: ResumeData, job: JobData) -> float:
    """
    Computes the semantic similarity between a resume and a job posting
    using OpenAI text-embedding-3-small and cosine similarity.

    Steps:
    1. Build rich text representations of resume and job
    2. Get embedding vectors from OpenAI (1536 dims each)
    3. Compute cosine similarity between the two vectors
    4. Convert to a 0-100 percentage

    Cost: ~$0.000002 per call (essentially free with text-embedding-3-small)

    Returns:
        Semantic similarity score from 0.0 to 100.0
    """
    try:
        resume_text = build_resume_embed_text(resume)
        job_text = build_job_embed_text(job)

        resume_vec = embed_text(resume_text)
        job_vec = embed_text(job_text)

        similarity = cosine_similarity(resume_vec, job_vec)
        score = cosine_similarity_to_percentage(similarity)

        logger.info(f"Semantic similarity: {similarity:.4f} → {score:.1f}%")
        return score

    except Exception as e:
        # If embedding fails for any reason (network, API key issue, etc.)
        # we gracefully fall back to AI-only scoring rather than crashing
        logger.warning(f"Semantic similarity computation failed, falling back to AI-only scoring: {e}")
        return None


def analyze_resume_against_job(
    resume: ResumeData,
    job: JobData,
) -> AnalysisResult:
    """
    Takes a ResumeData and JobData object.
    
    Two-stage scoring pipeline:
    1. RAG Semantic Score: Embeds both resume and job, computes cosine similarity
       → measures overall semantic overlap (catches synonyms, concept overlap)
    2. AI Weighted Score: Sends both to GPT for structured criteria evaluation
       → measures specific skill match, experience fit, education, projects
    
    Final score = 35% semantic + 65% AI weighted
    
    Returns a complete AnalysisResult object including semantic_similarity field.
    """

    # ── Stage 1: Semantic Similarity (RAG) ────────────────────────────────────
    # Runs before the GPT analysis call. Fast, cheap ($0.000002 per pair).
    semantic_score = compute_semantic_similarity(resume, job)
    logger.info(f"[analyzer] Semantic score: {semantic_score}")

    # ── Stage 2: GPT Structured Analysis ──────────────────────────────────────
    prompt = ANALYSIS_PROMPT.format(
        # Resume fields
        name=resume.name,
        skills=", ".join(resume.skills),
        experience=", ".join(
            [f"{e.role} at {e.company} ({e.duration})" for e in resume.experience]
        ),
        projects=", ".join(
            [f"{p.name} ({', '.join(p.tech_stack)})" for p in resume.projects]
        ),
        education=", ".join(
            [f"{e.degree} in {e.field} from {e.college}" for e in resume.education]
        ),
        total_experience_years=resume.total_experience_years,
        certifications=", ".join(resume.certifications),

        # Job fields
        job_title=job.title,
        job_company=job.company,
        required_skills=", ".join(job.required_skills),
        preferred_skills=", ".join(job.preferred_skills),
        experience_required=job.experience_required,
        education_required=job.education_required,
        job_description=job.description,
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You are an expert technical recruiter. Always respond with valid JSON only."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0,
        max_tokens=3000,
        seed=42,
    )

    raw_response = response.choices[0].message.content
    clean_response = clean_json_response(raw_response)
    data = json.loads(clean_response)

    if not isinstance(data, dict):
        raise ValueError(
            f"Resume analysis failed: AI returned '{type(data).__name__}' instead of a JSON object. "
            "This usually means the job description was too short or unreadable."
        )

    # ── Safe helpers — handle null JSON values ─────────────────────────────────
    def _safe_float(key: str) -> float:
        v = data.get(key)
        try:
            return float(v) if v is not None else 0.0
        except (TypeError, ValueError):
            return 0.0

    def _safe_list(key: str) -> list:
        v = data.get(key)
        return v if isinstance(v, list) else []

    def _safe_str(key: str) -> str:
        v = data.get(key)
        return str(v) if v is not None else ""

    # ── Stage 3: Blend scores ──────────────────────────────────────────────────
    # calculate_match_percentage blends ai_score and semantic_score internally
    match_percentage = calculate_match_percentage(
        required_skills_score=_safe_float("required_skills_score"),
        preferred_skills_score=_safe_float("preferred_skills_score"),
        experience_score=_safe_float("experience_score"),
        education_score=_safe_float("education_score"),
        projects_score=_safe_float("project_score"),
        semantic_score=semantic_score,  # ← RAG score injected here
    )

    logger.info(f"[analyzer] Final blended match: {match_percentage}%")

    # ── Build skill gap objects ────────────────────────────────────────────────
    missing_skills = [
        SkillGap(
            skill=str(s.get("skill") or ""),
            importance=str(s.get("importance") or "nice-to-have"),
            reason=str(s.get("reason") or "")
        )
        for s in _safe_list("missing_skills")
        if isinstance(s, dict)
    ]

    # ── Build and return the final AnalysisResult ──────────────────────────────
    result = AnalysisResult(
        match_percentage=match_percentage,
        semantic_similarity=semantic_score if semantic_score is not None else 0.0,
        matched_skills=_safe_list("matched_skills"),
        missing_skills=missing_skills,
        bonus_skills=_safe_list("bonus_skills"),
        experience_fit=_safe_str("experience_fit"),
        summary=_safe_str("summary"),
        resume_tips=_safe_list("resume_tips"),
    )

    return result
