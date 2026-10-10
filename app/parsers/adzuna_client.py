# app/parsers/adzuna_client.py

import httpx
from app.config import settings
from app.models.schemas import JobListing

ADZUNA_BASE_URL = "https://api.adzuna.com/v1/api/jobs"


async def search_adzuna_jobs(
    query: str,
    location: str = "",
    results_per_page: int = 5,
    remote_only: bool = False,
) -> list[JobListing]:
    """
    Searches Adzuna API for jobs matching the query.
    Returns a list of JobListing objects.
    """

    url = f"{ADZUNA_BASE_URL}/in/search/1"

    
    # Add location to search query instead of where filter
    # Adzuna's where filter doesn't work well for Indian cities
    if location:
        search_query = f"{query} {location}"
    else:
        search_query = query

    if remote_only:
        search_query = f"{search_query} remote"

    # Build base params — no location by default
    params = {
        "app_id": settings.adzuna_app_id,
        "app_key": settings.adzuna_app_key,
        "results_per_page": results_per_page,
        "what": search_query,
        "content-type": "application/json",
    }


    jobs = []

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()  # ← fixed: added ()
            data = response.json()

            for item in data.get("results", []):
                job = JobListing(
                    title=item.get("title", ""),
                    company=(item.get("company") or {}).get("display_name", ""),
                    location=(item.get("location") or {}).get("display_name", ""),
                    url=item.get("redirect_url", ""),
                    description=item.get("description", ""),
                    salary=_format_salary(
                        item.get("salary_min"),
                        item.get("salary_max")
                    ),
                    source="adzuna",
                    posted_date=item.get("created", ""),
                )
                jobs.append(job)

    except Exception as e:
        print(f"Adzuna search failed: {e}")

    return jobs


def _format_salary(salary_min, salary_max) -> str:
    if salary_min and salary_max:
        return f"{salary_min:,.0f} - {salary_max:,.0f}"
    elif salary_min:
        return f"From {salary_min:,.0f}"
    elif salary_max:
        return f"Up to {salary_max:,.0f}"
    return ""