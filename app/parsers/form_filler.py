# app/parsers/form_filler.py

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from app.models.schemas import ApplicationData, ApplyResponse


# ─── Field selectors for common form fields ───────────────────────────────────
# We try multiple selectors for each field
# because different websites use different naming conventions

FIELD_SELECTORS = {
    "full_name": [
        'input[name="name"]',
        'input[name="full_name"]',
        'input[name="fullName"]',
        'input[name="applicant_name"]',
        'input[placeholder*="name" i]',
        'input[id*="name" i]',
        'input[aria-label*="name" i]',
        'input[label*="name" i]',
    ],
    "email": [
        'input[type="email"]',
        'input[name="email"]',
        'input[name="email_address"]',
        'input[placeholder*="email" i]',
        'input[id*="email" i]',
        'input[aria-label*="email" i]',
    ],
    "phone": [
        'input[type="tel"]',
        'input[name="phone"]',
        'input[name="mobile"]',
        'input[name="phone_number"]',
        'input[name="contact"]',
        'input[placeholder*="phone" i]',
        'input[placeholder*="mobile" i]',
        'input[id*="phone" i]',
        'input[aria-label*="phone" i]',
    ],
    "experience": [
        'input[name="experience"]',
        'input[name="years_of_experience"]',
        'input[name="total_experience"]',
        'input[placeholder*="experience" i]',
        'input[id*="experience" i]',
        'select[name="experience"]',
        'select[id*="experience" i]',
    ],
    "cover_letter": [
        'textarea[name="cover_letter"]',
        'textarea[name="coverLetter"]',
        'textarea[name="message"]',
        'textarea[name="letter"]',
        'textarea[placeholder*="cover" i]',
        'textarea[placeholder*="letter" i]',
        'textarea[id*="cover" i]',
        'textarea[aria-label*="cover" i]',
    ],
    "skills": [
        'textarea[name="skills"]',
        'input[name="skills"]',
        'textarea[placeholder*="skills" i]',
        'input[placeholder*="skills" i]',
        'textarea[id*="skills" i]',
    ],
}

# ─── Portal specific URL patterns ─────────────────────────────────────────────

PORTAL_PATTERNS = {
    "linkedin": "linkedin.com",
    "naukri": "naukri.com",
    "indeed": "indeed.com",
    "glassdoor": "glassdoor.co",
    "internshala": "internshala.com",
}


def detect_portal(url: str) -> str:
    """
    Detects which job portal the URL belongs to.
    Returns portal name or 'generic' if unknown.
    """
    url_lower = url.lower()
    for portal, pattern in PORTAL_PATTERNS.items():
        if pattern in url_lower:
            return portal
    return "generic"


def fill_job_application(
    job_url: str,
    application_data: ApplicationData,
) -> ApplyResponse:
    """
    Opens the job application page and pre-fills
    all form fields it can find.
    Returns ApplyResponse with what was filled.
    """

    fields_filled = []
    fields_failed = []

    # Detect which portal this is
    portal = detect_portal(job_url)

    with sync_playwright() as p:
        # Launch browser in NON-headless mode
        # User needs to see the browser to review and submit
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        page.set_extra_http_headers({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })

        # Navigate to job application page
        page.goto(job_url, wait_until="networkidle", timeout=30000)

        # Wait for page to fully load
        page.wait_for_timeout(2000)

        # Fill fields based on portal
        if portal == "naukri":
            fields_filled, fields_failed = _fill_naukri(
                page, application_data
            )
        elif portal == "linkedin":
            fields_filled, fields_failed = _fill_linkedin(
                page, application_data
            )
        else:
            # Generic handler for all other portals
            fields_filled, fields_failed = _fill_generic(
                page, application_data
            )

        # Keep browser open for user to review and submit
        # We wait 5 minutes before closing automatically
        print("\n✅ Form pre-filled. Please review and submit in the browser.")
        print("Browser will stay open for 5 minutes.")
        page.wait_for_timeout(300000)  # 5 minutes in milliseconds

        browser.close()

    return ApplyResponse(
        success=True,
        job_url=job_url,
        application_data=application_data,
        fields_filled=fields_filled,
        fields_failed=fields_failed,
        message=f"Pre-filled {len(fields_filled)} fields. Please review and submit."
    )


def _fill_generic(page, data: ApplicationData) -> tuple[list, list]:
    """
    Generic form filler that works on most websites.
    Tries multiple selectors for each field.
    """
    fields_filled = []
    fields_failed = []

    # Map field names to their values
    field_values = {
        "full_name": data.full_name,
        "email": data.email,
        "phone": data.phone,
        "experience": str(data.total_experience_years),
        "cover_letter": data.cover_letter,
        "skills": data.skills_summary,
    }

    for field_name, value in field_values.items():
        if not value:
            fields_failed.append(field_name)
            continue

        filled = _try_fill_field(
            page,
            FIELD_SELECTORS[field_name],
            value,
        )

        if filled:
            fields_filled.append(field_name)
        else:
            fields_failed.append(field_name)

    return fields_filled, fields_failed


def _fill_naukri(page, data: ApplicationData) -> tuple[list, list]:
    """
    Naukri specific form filler.
    Naukri has a consistent apply form structure.
    """
    fields_filled = []
    fields_failed = []

    # Naukri specific selectors
    naukri_fields = {
        "full_name": ['input[placeholder="Enter your name"]',
                      'input[name="name"]'],
        "email": ['input[placeholder="Enter your email"]',
                  'input[type="email"]'],
        "phone": ['input[placeholder="Enter your mobile number"]',
                  'input[type="tel"]'],
        "cover_letter": ['textarea[placeholder*="cover" i]',
                         'textarea[name="message"]'],
    }

    field_values = {
        "full_name": data.full_name,
        "email": data.email,
        "phone": data.phone,
        "cover_letter": data.cover_letter,
    }

    for field_name, value in field_values.items():
        if not value:
            fields_failed.append(field_name)
            continue

        filled = _try_fill_field(
            page,
            naukri_fields[field_name],
            value,
        )

        if filled:
            fields_filled.append(field_name)
        else:
            fields_failed.append(field_name)

    return fields_filled, fields_failed


def _fill_linkedin(page, data: ApplicationData) -> tuple[list, list]:
    """
    LinkedIn Easy Apply form filler.
    LinkedIn has a multi-step apply form.
    """
    fields_filled = []
    fields_failed = []

    # Click Easy Apply button if present
    try:
        easy_apply_btn = page.locator(
            'button:has-text("Easy Apply")'
        ).first
        if easy_apply_btn:
            easy_apply_btn.click()
            page.wait_for_timeout(2000)
    except Exception:
        pass

    # LinkedIn specific selectors
    linkedin_fields = {
        "phone": [
            'input[id*="phoneNumber"]',
            'input[placeholder*="phone" i]',
        ],
        "cover_letter": [
            'textarea[id*="coverLetter"]',
            'textarea[placeholder*="cover" i]',
        ],
    }

    field_values = {
        "phone": data.phone,
        "cover_letter": data.cover_letter,
    }

    for field_name, value in field_values.items():
        if not value:
            fields_failed.append(field_name)
            continue

        filled = _try_fill_field(
            page,
            linkedin_fields[field_name],
            value,
        )

        if filled:
            fields_filled.append(field_name)
        else:
            fields_failed.append(field_name)

    return fields_filled, fields_failed


def _try_fill_field(
    page,
    selectors: list[str],
    value: str,
) -> bool:
    """
    Tries each selector one by one until one works.
    Returns True if field was filled, False if all selectors failed.
    """
    for selector in selectors:
        try:
            # Check if element exists and is visible
            element = page.locator(selector).first
            if element.is_visible(timeout=1000):
                # Clear existing content and type new value
                element.clear()
                element.fill(value)
                return True
        except Exception:
            continue

    return False