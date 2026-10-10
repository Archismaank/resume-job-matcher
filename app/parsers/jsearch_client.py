# app/parsers/jsearch_client.py

import httpx
from app.config import settings
from app.models.schemas import JobListing

JSEARCH_BASE_URL = "https://jsearch.p.rapidapi.com/search"


async def search_jsearch_jobs(
    query: str,
    location: str = "",
    num_pages: int = 2,
    employment_type: str = "FULLTIME",
    remote_only: bool = False,
) -> list[JobListing]:
    """
    Searches JSearch API (via RapidAPI) for jobs matching the query.
    JSearch aggregates jobs from LinkedIn, Indeed, Glassdoor and more.
    Returns a list of JobListing objects.
    """

    headers = {
        "X-RapidAPI-Key": settings.jsearch_api_key,
        "X-RapidAPI-Host": "jsearch.p.rapidapi.com",
    }

    # Build search query
    if location:
    # For broad countries like India don't append to query
    # Use it as context only for very specific cities
        broad_locations = ["india", "usa", "uk", "us", "united states", "united kingdom"]
        if location.lower() in broad_locations:
            search_query = query  # keep query clean for broad countries
        else:
            search_query = f"{query} in {location}"  # append for specific cities
    else:
        search_query = query

    params = {
        "query": search_query,
        "page": "1",                                    # must be string
        "num_pages": str(num_pages),
        "date_posted": "month",
        "remote_jobs_only": "true" if remote_only else "false",
        "employment_types": employment_type,
    }

    jobs = []

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                JSEARCH_BASE_URL,
                headers=headers,
                params=params
            )
            response.raise_for_status()
            data = response.json()

            for item in data.get("data", []):
                required, preferred = _extract_skills(
                    item.get("job_highlights", {})
                )

                # Format location — fallback to job_location if city/state empty
                location_str = _format_location(
                    item.get("job_city", ""),
                    item.get("job_state", ""),
                    item.get("job_country", ""),
                ) or item.get("job_location", "")

                job = JobListing(
                    title=item.get("job_title", ""),
                    company=item.get("employer_name", ""),
                    location=location_str,
                    url=item.get("job_apply_link", ""),
                    description=item.get("job_description", ""),
                    required_skills=required,
                    preferred_skills=preferred,
                    experience_required=_extract_experience(
                        item.get("job_description", "")
                    ),
                    education_required=(item.get("job_required_education") or {}).get("postgraduate_degree", ""),
                    salary=_format_jsearch_salary(item),
                    source="jsearch",
                    posted_date=item.get("job_posted_at_datetime_utc", ""),
                )
                jobs.append(job)

    except Exception as e:
        print(f"JSearch search failed: {e}")

    return jobs


def _format_location(city: str, state: str, country: str) -> str:
    """
    Combines city, state, country into a readable location string.
    """
    parts = [p for p in [city, state, country] if p]
    return ", ".join(parts)


def _extract_skills(job_highlights: dict) -> tuple[list[str], list[str]]:
    """
    Extracts required and preferred skills from JSearch job highlights.
    Returns a tuple of (required_skills, preferred_skills).
    """
    required_skills = []
    preferred_skills = []

    preferred_keywords = [
        # Direct preferred indicators
        "preferred", "preference",
        "nice to have", "nice-to-have",
        "good to have", "good-to-have",

        # Bonus/plus indicators
        "bonus", "plus", "added advantage",
        "added bonus", "extra credit",

        # Optional indicators
        "optional", "not required",
        "not mandatory",

        # Desirable indicators
        "desirable", "desired",
        "ideally", "ideal candidate",

        # Welcome/appreciate indicators
        "welcome", "welcomed",
        "appreciated", "appreciate",
        "value", "valued",

        # Helpful indicators
        "helpful", "would help",
        "beneficial", "benefit",

        # Familiarity indicators
        "familiarity", "familiar with",
        "exposure to", "exposure",

        # Soft preferred indicators
        "great if", "would be great",
        "we'd love", "we would love",
        "strong plus", "big plus",
    ]

    qualifications = job_highlights.get("Qualifications", [])

    for qual in qualifications:
        if not qual:
            continue

        qual_lower = qual.lower()
        is_preferred = any(
            keyword in qual_lower
            for keyword in preferred_keywords
        )

        if is_preferred:
            preferred_skills.append(qual)
        else:
            required_skills.append(qual)

    return required_skills, preferred_skills


def _extract_experience(description: str) -> str:
    """
    Extracts experience requirement from job description.
    Uses regex for common patterns first (fast + free).
    Falls back to empty string for OpenAI to handle during analysis.
    """
    import re

    if not description:
        return ""

    patterns = [
        r'\d+\+?\s*(?:to|-)\s*\d+\s*years?',
        r'\d+\+\s*years?',
        r'\d+\s*years?\s*of\s*experience',
        r'experience\s*:\s*\d+\s*(?:to|-)?\s*\d*\s*years?',
        r'\d+\s*yrs?',
        r'fresher|entry.?level|0.?1\s*year',
        r'senior|mid.?level|junior',
        r'minimum\s+\d+\s*years?',
        r'at\s+least\s+\d+\s*years?',
    ]

    for pattern in patterns:
        match = re.search(pattern, description, re.IGNORECASE)
        if match:
            return match.group(0)

    return ""


def _format_jsearch_salary(item: dict) -> str:
    """
    Formats salary from JSearch response fields.
    """
    salary_min = item.get("job_min_salary")
    salary_max = item.get("job_max_salary")
    salary_period = item.get("job_salary_period", "")

    if salary_min and salary_max:
        return f"{salary_min:,.0f} - {salary_max:,.0f} {salary_period}"
    elif salary_min:
        return f"From {salary_min:,.0f} {salary_period}"
    elif salary_max:
        return f"Up to {salary_max:,.0f} {salary_period}"
    return ""