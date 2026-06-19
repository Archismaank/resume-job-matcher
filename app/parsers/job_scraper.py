from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import re

# Maximum characters to pass to the AI extractor.
# Job descriptions are rarely longer than this — cutting here removes
# the "Similar Jobs" / "Recommended" sections that appear at the bottom
# of most job portal pages (Naukri, LinkedIn, Indeed, etc.)
_MAX_TEXT_CHARS = 5000

# HTML tags that are pure UI chrome — never contain job requirements
_NOISE_TAGS = [
    "script", "style", "header", "footer", "nav",
    "aside", "form", "button", "svg", "iframe", "noscript",
]

# CSS class / id substrings whose containing elements are almost always noise.
# BeautifulSoup will remove any tag whose class or id contains one of these.
_NOISE_PATTERNS = [
    "similar", "recommend", "related", "suggested",
    "other-job", "more-job", "job-list", "trending",
    "cookie", "banner", "popup", "modal", "overlay",
    "advertisement", "promo", "signup", "login",
    "sidebar", "widget", "breadcrumb",
]


def _remove_noise_elements(soup: BeautifulSoup) -> None:
    """Remove tags that are structurally noise (nav, aside, etc.)."""
    for tag in soup(_NOISE_TAGS):
        tag.decompose()

    # Remove elements whose class or id strongly suggests sidebar / related-jobs noise
    for element in soup.find_all(True):
        classes = " ".join(element.get("class", [])).lower()
        element_id = (element.get("id") or "").lower()
        combined = classes + " " + element_id
        if any(pattern in combined for pattern in _NOISE_PATTERNS):
            element.decompose()


def _extract_clean_text(soup: BeautifulSoup) -> str:
    """Convert the cleaned soup to readable plain text, then trim."""
    text = soup.get_text(separator="\n")

    # Collapse blank lines and strip whitespace per line
    lines = [line.strip() for line in text.splitlines()]
    non_empty = [line for line in lines if line]

    # Remove very short lines that are usually nav remnants ("Home", ">", "|", etc.)
    meaningful = [line for line in non_empty if len(line) > 3]

    clean_text = "\n".join(meaningful)

    # Truncate to keep only the main job body — similar-jobs sections
    # are almost always in the lower half of the page
    return clean_text[:_MAX_TEXT_CHARS]


def scrape_job_posting(url: str) -> str:
    """
    Takes a job posting URL and returns focused, clean text of just the
    job description — with noise (similar jobs, sidebars, banners) removed.

    Runs via sync_playwright inside asyncio.to_thread() in routes.py
    so it never conflicts with the asyncio event loop.
    """

    if not url.startswith("http"):
        raise ValueError(f"Invalid URL: {url}. Must start with http or https.")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Realistic user-agent to avoid bot-detection blocks
        page.set_extra_http_headers({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        })

        page.goto(url, wait_until="networkidle", timeout=30000)
        html = page.content()
        browser.close()

    soup = BeautifulSoup(html, "html.parser")
    _remove_noise_elements(soup)
    return _extract_clean_text(soup)


def scrape_job_posting_fallback(job_text: str) -> str:
    """
    Simple fallback — returns raw job text as-is when no URL is provided.
    """
    return job_text.strip()