from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth
from bs4 import BeautifulSoup

from app.models.schemas import JobListing


def search_naukri_jobs(
    query: str,
    location: str = "",
    experience: str = "0",
    remote_only: bool = False,
    employment_type: str = "FULLTIME",
) -> list[JobListing]:
    """
    Scrapes Naukri.com for jobs matching the query.
    Returns a list of JobListing objects.
    """

    jobs = []

    try:
        url = _build_naukri_url(
            query=query,
            location=location,
            experience=experience,
        )

        with Stealth().use_sync(sync_playwright()) as p:

            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                ],
            )

            context = browser.new_context(
                viewport={
                    "width": 1366,
                    "height": 768,
                },
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/137.0.0.0 Safari/537.36"
                ),
                locale="en-US",
                timezone_id="Asia/Kolkata",
                java_script_enabled=True,
            )

            page = context.new_page()

            try:
                page.goto(
                    url,
                    wait_until="domcontentloaded",
                    timeout=30000,
                )

                page.wait_for_timeout(3000)

            except Exception:
                browser.close()
                return []

            html = None

            for selector in [
                ".srp-jobtuple-wrapper",
                ".jobTuple",
                "[class*='jobtuple']",
            ]:
                try:
                    page.wait_for_selector(
                        selector,
                        timeout=8000,
                    )

                    html = page.content()
                    break

                except Exception:
                    continue
            
            context.close()
            browser.close()

            if not html:
                return []

        soup = BeautifulSoup(html, "html.parser")

        job_cards = (
            soup.find_all(
                "div",
                class_="srp-jobtuple-wrapper",
            )
            or soup.find_all(
                "article",
                class_="jobTuple",
            )
            or []
        )

        for card in job_cards:
            job = _parse_naukri_job_card(
                card,
                remote_only,
            )

            if job:
                jobs.append(job)

    except Exception:
        return []

    return jobs


def _build_naukri_url(
    query: str,
    location: str,
    experience: str,
) -> str:
    """
    Builds a Naukri search URL from query parameters.
    """

    query_slug = query.lower().strip().replace(" ", "-")

    url = f"https://www.naukri.com/{query_slug}-jobs"

    if location:
        location_slug = (
            location.lower()
            .strip()
            .replace(" ", "-")
        )

        url = (
            f"https://www.naukri.com/"
            f"{query_slug}-jobs-in-{location_slug}"
        )

    url += f"?experience={experience}"

    return url


def _parse_naukri_job_card(
    card,
    remote_only: bool,
) -> JobListing | None:
    """
    Parses a single Naukri job card.
    """

    try:
        title_tag = card.find(
            "a",
            class_="title",
        )

        title = (
            title_tag.get_text(strip=True)
            if title_tag
            else ""
        )

        if not title:
            return None

        url = title_tag.get(
            "href",
            "",
        )

        company_tag = card.find(
            "a",
            class_="comp-name",
        )

        company = (
            company_tag.get(
                "title",
                "",
            )
            if company_tag
            else ""
        )

        exp_tag = card.find(
            "span",
            class_="expwdth",
        )

        experience = (
            exp_tag.get_text(strip=True)
            if exp_tag
            else ""
        )

        loc_tag = card.find(
            "span",
            class_="locWdth",
        )

        location = (
            loc_tag.get_text(strip=True)
            if loc_tag
            else ""
        )

        if (
            remote_only
            and "remote" not in location.lower()
        ):
            return None

        desc_tag = card.find(
            "span",
            class_="job-desc",
        )

        description = (
            desc_tag.get_text(strip=True)
            if desc_tag
            else ""
        )

        skills_container = card.find(
            "ul",
            class_="tags-gt",
        )

        skills = []

        if skills_container:
            skill_tags = skills_container.find_all(
                "li",
                class_="tag-li",
            )

            skills = [
                skill.get_text(strip=True)
                for skill in skill_tags
                if skill.get_text(strip=True)
            ]

        date_tag = card.find(
            "span",
            class_="job-post-day",
        )

        posted_date = (
            date_tag.get_text(strip=True)
            if date_tag
            else ""
        )

        return JobListing(
            title=title,
            company=company,
            location=location,
            url=url,
            description=description,
            required_skills=skills,
            experience_required=experience,
            source="naukri",
            posted_date=posted_date,
        )

    except Exception:
        return None