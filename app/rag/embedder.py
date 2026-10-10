# app/rag/embedder.py
"""
Embedding utility using OpenAI text-embedding-3-small.

Why text-embedding-3-small?
- Cost: $0.02 per 1M tokens (≈ $0.000002 per resume+job pair — essentially free)
- Quality: 1536-dim vectors, excellent semantic understanding
- Speed: ~200ms per call
- No extra dependencies — uses the openai package already in the project

Usage:
    from app.rag.embedder import embed_text, embed_batch, build_resume_embed_text, build_job_embed_text
"""

import logging
from openai import OpenAI
from app.config import settings

logger = logging.getLogger(__name__)

# Reuse one OpenAI client across all calls (same pattern as analyzer.py)
_client = OpenAI(api_key=settings.openai_api_key)

EMBEDDING_MODEL = "text-embedding-3-small"


def embed_text(text: str) -> list[float]:
    """
    Converts a single text string into a 1536-dimensional embedding vector.

    Args:
        text: Any text string (resume snippet, job description, etc.)

    Returns:
        A list of 1536 floats representing the semantic meaning of the text.
    """
    # Truncate to 8000 chars to stay well within the 8192 token limit
    truncated = text[:8000].strip()
    if not truncated:
        # Return a zero vector if text is empty — similarity will be 0
        return [0.0] * 1536

    response = _client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=truncated,
    )
    return response.data[0].embedding


def embed_batch(texts: list[str]) -> list[list[float]]:
    """
    Converts a list of text strings into embedding vectors in a single API call.
    Much more efficient than calling embed_text() in a loop.

    Args:
        texts: List of text strings to embed.

    Returns:
        List of embedding vectors, in the same order as the input texts.
    """
    if not texts:
        return []

    # Truncate each text and replace empty strings with a placeholder
    truncated = [t[:8000].strip() or " " for t in texts]

    response = _client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=truncated,
    )

    # Ensure results are returned in input order (OpenAI guarantees order but be safe)
    results = sorted(response.data, key=lambda d: d.index)
    return [r.embedding for r in results]


def build_resume_embed_text(resume) -> str:
    """
    Builds a rich text representation of a ResumeData object for embedding.

    We concatenate the most semantically meaningful parts:
    - Skills (most important for job matching)
    - Experience roles and descriptions
    - Project names and tech stacks
    - Certifications

    We deliberately exclude: name, email, phone (not semantically relevant).
    """
    parts = []

    # Skills — highest weight, listed first
    if resume.skills:
        parts.append("Skills: " + ", ".join(resume.skills))

    # Experience — role titles and what they did
    for exp in resume.experience:
        exp_text = f"{exp.role}"
        if exp.company:
            exp_text += f" at {exp.company}"
        if exp.description:
            exp_text += f": {exp.description}"
        parts.append(exp_text)

    # Projects — name + tech stack
    for proj in resume.projects:
        proj_text = proj.name
        if proj.tech_stack:
            proj_text += " using " + ", ".join(proj.tech_stack)
        if proj.description:
            proj_text += f". {proj.description}"
        parts.append(proj_text)

    # Certifications
    if resume.certifications:
        parts.append("Certifications: " + ", ".join(resume.certifications))

    return " | ".join(parts)


def build_job_embed_text(job) -> str:
    """
    Builds a rich text representation of a JobData object for embedding.

    Concatenates:
    - Required skills (most important)
    - Preferred skills
    - Job title + company
    - Job description
    """
    parts = []

    if job.title:
        parts.append(f"Role: {job.title}")

    if job.required_skills:
        parts.append("Required: " + ", ".join(job.required_skills))

    if job.preferred_skills:
        parts.append("Preferred: " + ", ".join(job.preferred_skills))

    if job.experience_required:
        parts.append(f"Experience: {job.experience_required}")

    if job.description:
        parts.append(job.description)

    return " | ".join(parts)
