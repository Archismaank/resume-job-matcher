# ui/streamlit_app.py

import streamlit as st
import requests
import json
import io
from datetime import datetime
from fpdf import FPDF
from streamlit_extras.metric_cards import style_metric_cards
from ui.components import (
    set_page_config,
    render_header,
    render_global_resume_uploader,
    render_match_score,
    render_skills_section,
    render_resume_tips,
    render_summary,
    render_job_card,
)
from ui.auth.login import render_login_page, logout

API_URL = "http://localhost:8000/api/v1"

# ─── Location and Employment Type Options ─────────────────────────────────────

POPULAR_LOCATIONS = [
    "Anywhere (Global)",
    "India (All cities)",
    "Bangalore",
    "Mumbai",
    "Delhi / NCR",
    "Hyderabad",
    "Chennai",
    "Pune",
    "Kolkata",
    "Ahmedabad",
    "Noida",
    "Gurgaon",
    "Remote",
    "United States",
    "United Kingdom",
    "Canada",
    "Australia",
    "Singapore",
    "Dubai / UAE",
    "Germany",
    "Netherlands",
    "Type a custom location...",
]

EMPLOYMENT_TYPES = {
    "Full Time": "FULLTIME",
    "Part Time": "PARTTIME",
    "Internship": "INTERN",
    "Contract": "CONTRACTOR",
}


def main():
    set_page_config()

    # ── Restore session from query param token (survives page refresh) ────────
    if not st.session_state.get("access_token"):
        token = st.query_params.get("token")
        if token:
            try:
                resp = requests.get(
                    f"{API_URL}/auth/me",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=5,
                )
                if resp.status_code == 200:
                    user = resp.json()
                    st.session_state.access_token = token
                    st.session_state.user_id      = user.get("id")
                    st.session_state.user_name    = user.get("name")
                    st.session_state.user_email   = user.get("email")
                else:
                    # Token expired or invalid — clear it
                    st.query_params.clear()
            except Exception:
                st.query_params.clear()

    # ── Auth gate ────────────────────────────────────────────────────────────
    if not st.session_state.get("access_token"):
        render_login_page()
        return

    # ── Logged-in session setup ───────────────────────────────────────────────
    if "resume_file" not in st.session_state:
        st.session_state.resume_file = None

    if "resume_name" not in st.session_state:
        st.session_state.resume_name = None

    # ── Top bar: user info + logout ─────────────────────────────────────────
    user_col, logout_col = st.columns([5, 1])
    with user_col:
        st.markdown(f"""
        <div style="padding: 10px 0 4px 0; display:flex; align-items:center; gap:10px;">
            <span style="background:rgba(201,168,76,0.12); border:1px solid rgba(201,168,76,0.25);
                         border-radius:999px; padding:4px 14px; font-size:12.5px;
                         font-family:'DM Sans',sans-serif; color:#e2c97e; font-weight:600;
                         letter-spacing:0.3px;">
                ✦ &nbsp; {st.session_state.get('user_name', '')}
            </span>
            <span style="color:#4a4030; font-size:12.5px; font-family:'DM Sans',sans-serif;">
                {st.session_state.get('user_email', '')}
            </span>
        </div>
        """, unsafe_allow_html=True)
    with logout_col:
        st.markdown("<div style='padding-top:8px;'>", unsafe_allow_html=True)
        if st.button("Sign Out", use_container_width=True):
            logout()
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    render_header()

    st.markdown("<br>", unsafe_allow_html=True)

    render_global_resume_uploader()

    st.markdown("<br>", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs([
        "1️⃣  Analyze",
        "2️⃣  Find Jobs",
        "3️⃣  Apply",
    ])

    with tab1:
        render_analyze_page()

    with tab2:
        render_recommend_page()

    with tab3:
        render_apply_page()


def _page_intro(title: str, subtitle: str):
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style="margin-bottom: 8px;">
        <h2 class="grad-text" style="font-size: 30px; font-weight: 700; letter-spacing: -0.5px; margin: 0; font-family:'Playfair Display',serif;">{title}</h2>
        <p style="color: #6a6050; margin-top: 8px; font-size: 15.5px; line-height:1.7; max-width:720px; font-family:'DM Sans',sans-serif;">{subtitle}</p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")


def render_analyze_page():
    _page_intro(
        "Analyze a specific job posting",
        "See how well your resume matches a job — get a score, skill gaps, and tips."
    )

    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        _section_label("📄", "Resume Status")

        resume_file = st.session_state.resume_file

        if resume_file:
            st.success(f"✓ {resume_file.name}")
        else:
            st.warning("Upload your resume above.")

    with col2:
        _section_label("🔗", "Job Details")
        input_type = st.radio(
            "input_type",
            ["Paste a URL", "Paste job description"],
            horizontal=True,
            label_visibility="collapsed"
        )
        st.markdown("<br>", unsafe_allow_html=True)
        if input_type == "Paste a URL":
            job_input = st.text_input(
                "job_url",
                placeholder="https://naukri.com/job-listings-python-developer...",
                label_visibility="collapsed"
            )
        else:
            job_input = st.text_area(
                "job_desc",
                placeholder="Paste the full job description here...",
                height=160,
                label_visibility="collapsed"
            )

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("Analyze my resume →", use_container_width=True, type="primary"):
        if not resume_file:
            st.error("Please upload your resume.")
            return
        if not job_input:
            st.error("Please provide a job URL or description.")
            return
        # Clear only THIS section's previous result before new analysis
        st.session_state.pop("analyze_result", None)
        # Store the URL (or None) so the Apply/PDF sections can use it
        st.session_state.analyze_url = job_input if input_type == "Paste a URL" else None

        # ── URL result cache: same URL → same result, zero variance ──────────
        url_cache  = st.session_state.setdefault("url_result_cache", {})
        cache_key  = job_input if input_type == "Paste a URL" else None

        if cache_key and cache_key in url_cache:
            # Instant cache hit — no API call needed
            st.session_state.analyze_result = url_cache[cache_key]
            st.toast("Loaded from cache — results are consistent with your previous analysis.", icon="⚡")
        else:
            with st.spinner("Analyzing..."):
                result = _call_analyze_api(resume_file, job_input, input_type)
            if result:
                st.session_state.analyze_result = result
                if cache_key:
                    url_cache[cache_key] = result   # cache for future hits

    # Always render if result exists in session state
    if st.session_state.get("analyze_result"):
        _render_analysis_results(st.session_state.analyze_result)


def render_recommend_page():
    _page_intro(
        "Find jobs that match your resume",
        "We search Adzuna, JSearch, and Naukri simultaneously and rank results by how well they match your profile."
    )

    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        _section_label("📄", "Resume Status")

        resume_file = st.session_state.resume_file

        if resume_file:
            st.success(f"✓ {resume_file.name}")
        else:
            st.warning("Upload your resume above.")

    with col2:
        _section_label("⚙️", "Search Preferences")

        # Location dropdown
        location_choice = st.selectbox(
            "📍 Location",
            options=POPULAR_LOCATIONS,
            index=0,
        )

        # Handle location choice
        remote_only = False
        if location_choice == "Type a custom location...":
            location = st.text_input(
                "Enter your location",
                placeholder="e.g. Noida, Berlin, Tokyo..."
            )
        elif location_choice == "Anywhere (Global)":
            location = ""
        elif location_choice == "India (All cities)":
            location = "India"
        elif location_choice == "Remote":
            location = ""
            remote_only = True
        elif location_choice == "Delhi / NCR":
            location = "Delhi"
        elif location_choice == "Dubai / UAE":
            location = "Dubai"
        else:
            location = location_choice

        # Employment type dropdown
        employment_label = st.selectbox(
            "💼 Employment Type",
            options=list(EMPLOYMENT_TYPES.keys()),
            index=0,
        )
        employment_type = EMPLOYMENT_TYPES[employment_label]

        # Remote checkbox only if not already set by location
        if location_choice != "Remote":
            remote_only = st.checkbox("🌐 Remote jobs only")
        else:
            st.info("Searching remote jobs globally")

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("Find matching jobs →", use_container_width=True, type="primary"):
        if not resume_file:
            st.error("Please upload your resume.")
            return
        # Clear only THIS section's previous result before new search
        st.session_state.pop("recommend_result", None)
        with st.spinner("Searching across job portals..."):
            result = _call_recommend_api(
                resume_file, location, employment_type, remote_only
            )
        if result:
            st.session_state.recommend_result = result

    # Always render if result exists in session state
    if st.session_state.get("recommend_result"):
        _render_recommendations(st.session_state.recommend_result)


def render_apply_page():
    _page_intro(
        "Pre-fill a job application",
        "We open the application page in your browser and fill in your details automatically. You review and submit."
    )

    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        _section_label("📄", "Resume Status")

        resume_file = st.session_state.resume_file

        if resume_file:
            st.success(f"✓ {resume_file.name}")
        else:
            st.warning("Upload your resume above.")

    with col2:
        _section_label("🔗", "Job Details")

        # Check if pre-filled from a recommendation
        prefill = st.session_state.get("prefill_job", {})
        if prefill:
            st.markdown("""
            <div style="background:rgba(201,168,76,0.08); border:1px solid rgba(201,168,76,0.25);
                        border-radius:10px; padding:10px 14px; margin-bottom:12px;
                        font-family:'DM Sans',sans-serif; font-size:13px; color:#e2c97e;">
                ✦ &nbsp; Job details pre-filled from your recommendation.
            </div>
            """, unsafe_allow_html=True)

        job_url = st.text_input(
            "Application URL",
            value=prefill.get("url", ""),
            placeholder="https://naukri.com/job-listings-..."
        )
        job_title = st.text_input(
            "Job title",
            value=prefill.get("title", ""),
            placeholder="e.g. Python Developer"
        )
        job_company = st.text_input(
            "Company",
            value=prefill.get("company", ""),
            placeholder="e.g. Google"
        )

        # Clear prefill after reading so it doesn't re-populate on next visit
        if prefill:
            st.session_state.pop("prefill_job", None)

    st.markdown("<br>", unsafe_allow_html=True)

    st.info(
        "A browser window will open with your details pre-filled. "
        "Review everything carefully before clicking Submit."
    )

    if st.button("Open & pre-fill application →", use_container_width=True, type="primary"):
        if not resume_file:
            st.error("Please upload your resume.")
            return
        if not job_url:
            st.error("Please provide the application URL.")
            return
        with st.spinner("Generating cover letter and opening browser..."):
            result = _call_apply_api(
                resume_file, job_url, job_title, job_company
            )
        if result:
            _render_apply_results(result)


# ─── Helper ───────────────────────────────────────────────────────────────────

def _section_label(icon: str, label: str):
    st.markdown(f"""
    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 14px;">
        <span style="font-size: 18px; display:inline-flex; align-items:center; justify-content:center; width:34px; height:34px; border-radius:10px; background:linear-gradient(135deg, rgba(201,168,76,0.16), rgba(160,120,48,0.10)); border:1px solid rgba(201,168,76,0.28);">{icon}</span>
        <span style="font-family:'DM Sans',sans-serif; font-size: 11.5px; font-weight: 700; color: #7a7060; text-transform: uppercase; letter-spacing: 2px;">{label}</span>
    </div>
    """, unsafe_allow_html=True)


# ─── API Calls ────────────────────────────────────────────────────────────────

def _auth_headers() -> dict:
    """Returns the Authorization header using the token stored in session state."""
    token = st.session_state.get("access_token", "")
    return {"Authorization": f"Bearer {token}"}


def _handle_401():
    """Called when the backend returns 401 — token expired or invalid."""
    logout()
    st.error("Your session has expired. Please sign in again.")
    st.rerun()


def _call_analyze_api(resume_file, job_input: str, input_type: str):
    try:
        files = {"file": (resume_file.name, resume_file, resume_file.type)}
        headers = _auth_headers()
        if input_type == "Paste a URL":
            response = requests.post(
                f"{API_URL}/analyze/url",
                files=files,
                data={"job_url": job_input},
                headers=headers,
                timeout=120,
            )
        else:
            response = requests.post(
                f"{API_URL}/analyze/text",
                files=files,
                data={"job_text": job_input},
                headers=headers,
                timeout=120,
            )
        if response.status_code == 200:
            return response.json()
        if response.status_code == 401:
            _handle_401()
            return None
        st.error(f"Error: {response.json().get('detail', 'Unknown error')}")
        return None
    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to the backend. Make sure the server is running.")
        return None
    except Exception as e:
        st.error(f"Something went wrong: {str(e)}")
        return None


def _call_recommend_api(resume_file, location, employment_type, remote_only):
    try:
        files = {"file": (resume_file.name, resume_file, resume_file.type)}
        data = {
            "location": location,
            "employment_type": employment_type,
            "remote_only": str(remote_only).lower(),
        }
        response = requests.post(
            f"{API_URL}/recommend",
            files=files,
            data=data,
            headers=_auth_headers(),
            timeout=480,  # 8 min — AI analyzes 35 jobs which takes time
        )
        if response.status_code == 200:
            return response.json()
        if response.status_code == 401:
            _handle_401()
            return None
        st.error(f"Error: {response.json().get('detail', 'Unknown error')}")
        return None
    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to the backend. Make sure the server is running.")
        return None
    except Exception as e:
        st.error(f"Something went wrong: {str(e)}")
        return None


def _call_apply_api(resume_file, job_url, job_title, job_company):
    try:
        files = {"file": (resume_file.name, resume_file, resume_file.type)}
        data = {
            "job_url": job_url,
            "job_title": job_title,
            "job_company": job_company,
        }
        response = requests.post(
            f"{API_URL}/apply",
            files=files,
            data=data,
            headers=_auth_headers(),
            timeout=360,
        )
        if response.status_code == 200:
            return response.json()
        if response.status_code == 401:
            _handle_401()
            return None
        st.error(f"Error: {response.json().get('detail', 'Unknown error')}")
        return None
    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to the backend. Make sure the server is running.")
        return None
    except Exception as e:
        st.error(f"Something went wrong: {str(e)}")
        return None


def _generate_pdf_report(result: dict, job_url: str = None) -> bytes:
    """Generates a styled PDF analysis report and returns it as bytes."""
    job      = result.get("job", {}) or {}
    analysis = result.get("analysis", {}) or {}
    resume   = result.get("resume", {}) or {}
    match_pct   = analysis.get("match_percentage", 0)
    match_label = result.get("match_label", "")
    generated   = datetime.now().strftime("%B %d, %Y  %H:%M")

    # ── Colours ───────────────────────────────────────────────────────────────
    C_BG    = (18, 16, 10)
    C_GOLD  = (201, 168, 76)
    C_WHITE = (255, 255, 255)
    C_LIGHT = (240, 235, 220)
    C_GRAY  = (120, 112, 90)
    C_GREEN = (80, 160, 100)
    C_RED   = (180, 70, 70)
    C_BLUE  = (70, 130, 180)

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()
    pdf.set_margins(18, 18, 18)

    # ── Header bar ────────────────────────────────────────────────────────────
    pdf.set_fill_color(*C_BG)
    pdf.rect(0, 0, 210, 52, "F")

    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(*C_GOLD)
    pdf.set_y(11)
    pdf.cell(0, 11, "Resume Job Matcher", ln=True, align="C")

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*C_LIGHT)
    pdf.cell(0, 6, "AI-Powered Career Analysis Report", ln=True, align="C")

    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(*C_GRAY)
    pdf.cell(0, 5, f"Generated: {generated}", ln=True, align="C")
    pdf.ln(16)

    # ── Helper lambdas ────────────────────────────────────────────────────────
    def section_title(text):
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(*C_GOLD)
        pdf.set_fill_color(30, 26, 16)
        pdf.cell(0, 8, f"  {text}", ln=True, fill=True)
        pdf.ln(2)
        pdf.set_text_color(40, 36, 24)

    def body(text, indent=0):
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(50, 45, 35)
        pdf.set_x(18 + indent)
        pdf.multi_cell(0, 5, text)

    def kv(key, value, indent=0):
        if not value:
            return
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(*C_GRAY)
        pdf.set_x(18 + indent)
        pdf.cell(38, 5, key + ":", ln=False)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(50, 45, 35)
        pdf.multi_cell(0, 5, str(value))

    # ── Job Details ───────────────────────────────────────────────────────────
    section_title("JOB DETAILS")
    kv("Position",   job.get("title", "N/A"))
    kv("Company",    job.get("company", "N/A"))
    kv("Experience", job.get("experience_required", ""))
    kv("Education",  job.get("education_required", ""))
    if job_url:
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(*C_GRAY)
        pdf.set_x(18)
        pdf.cell(38, 5, "Source URL:", ln=False)
        pdf.set_font("Helvetica", "U", 8)
        pdf.set_text_color(*C_BLUE)
        pdf.multi_cell(0, 5, job_url)
    pdf.ln(4)

    # ── Match Score ───────────────────────────────────────────────────────────
    section_title("MATCH SCORE")
    pdf.set_font("Helvetica", "B", 28)
    pdf.set_text_color(*C_GOLD)
    pdf.cell(0, 14, f"{match_pct}%", ln=False, align="L")
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(*C_GRAY)
    pdf.cell(0, 14, match_label, ln=True, align="R")

    # Progress bar
    bar_x, bar_y, bar_w, bar_h = 18, pdf.get_y() + 1, 174, 5
    pdf.set_fill_color(40, 35, 20)
    pdf.rect(bar_x, bar_y, bar_w, bar_h, "F")
    fill_w = bar_w * (match_pct / 100)
    r = int(C_RED[0] + (C_GOLD[0] - C_RED[0]) * match_pct / 100)
    g = int(C_RED[1] + (C_GOLD[1] - C_RED[1]) * match_pct / 100)
    b = int(C_RED[2] + (C_GOLD[2] - C_RED[2]) * match_pct / 100)
    pdf.set_fill_color(r, g, b)
    pdf.rect(bar_x, bar_y, fill_w, bar_h, "F")
    pdf.set_y(bar_y + bar_h + 4)
    pdf.ln(4)

    # ── Candidate ─────────────────────────────────────────────────────────────
    section_title("CANDIDATE")
    kv("Name",       resume.get("name", ""))
    kv("Experience", f"{resume.get('total_experience_years', 0)} years")
    kv("Education",  ", ".join(
        [f"{e.get('degree','')} from {e.get('college','')}"
         for e in (resume.get("education") or [])]
    ))
    pdf.ln(4)

    # ── Summary ───────────────────────────────────────────────────────────────
    summary = analysis.get("summary", "")
    if summary:
        section_title("AI SUMMARY")
        body(summary)
        pdf.ln(4)

    # ── Matched Skills ────────────────────────────────────────────────────────
    matched = analysis.get("matched_skills", []) or []
    if matched:
        section_title(f"MATCHED SKILLS  ({len(matched)})")
        skills_line = "  |  ".join(matched)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*C_GREEN)
        pdf.multi_cell(0, 5, skills_line)
        pdf.ln(4)

    # ── Missing Skills ────────────────────────────────────────────────────────
    missing = analysis.get("missing_skills", []) or []
    if missing:
        section_title(f"MISSING SKILLS  ({len(missing)})")
        for s in missing:
            if not isinstance(s, dict):
                continue
            skill      = s.get("skill", "")
            importance = s.get("importance", "")
            reason     = s.get("reason", "")
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(*C_RED)
            pdf.set_x(22)
            tag = f"[{importance}]" if importance else ""
            pdf.cell(0, 5, f"- {skill}  {tag}", ln=True)
            if reason:
                pdf.set_font("Helvetica", "I", 8)
                pdf.set_text_color(*C_GRAY)
                pdf.set_x(28)
                pdf.multi_cell(0, 4, reason)
        pdf.ln(4)

    # ── Bonus Skills ──────────────────────────────────────────────────────────
    bonus = analysis.get("bonus_skills", []) or []
    if bonus:
        section_title(f"BONUS SKILLS  ({len(bonus)})")
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*C_BLUE)
        pdf.multi_cell(0, 5, "  |  ".join(bonus))
        pdf.ln(4)

    # ── Resume Tips ───────────────────────────────────────────────────────────
    tips = analysis.get("resume_tips", []) or []
    if tips:
        section_title("RESUME IMPROVEMENT TIPS")
        for i, tip in enumerate(tips, 1):
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(*C_GRAY)
            pdf.set_x(22)
            pdf.cell(6, 5, f"{i}.", ln=False)
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(50, 45, 35)
            pdf.multi_cell(0, 5, str(tip))
        pdf.ln(2)

    # ── Footer line ───────────────────────────────────────────────────────────
    pdf.set_draw_color(*C_GOLD)
    pdf.set_line_width(0.4)
    pdf.line(18, pdf.get_y(), 192, pdf.get_y())

    return bytes(pdf.output())


# ─── Results ──────────────────────────────────────────────────────────────────

def _render_analysis_results(result: dict):
    analysis = result.get("analysis", {})
    match_percentage = analysis.get("match_percentage", 0)
    match_label = result.get("match_label", "")
    match_color = result.get("match_color", "gray")

    st.markdown("---")
    st.markdown("""<h2 class="grad-text" style="font-size: 28px; font-weight: 700; letter-spacing: -0.5px; margin: 0 0 8px 0; font-family:'Playfair Display',serif;">Your results</h2>""", unsafe_allow_html=True)

    render_match_score(match_percentage, match_label, match_color)

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        matched = len(analysis.get("matched_skills", []))
        total = matched + len(analysis.get("missing_skills", []))
        st.metric("Match Score", f"{match_percentage}%", match_label)
    with col2:
        st.metric("Skills Matched", f"{matched}/{total}")
    with col3:
        exp_fit = analysis.get("experience_fit", "unknown")
        st.metric("Experience Fit", exp_fit.title())

    style_metric_cards(
        background_color="#12100a",
        border_left_color="#c9a84c",
        border_color="#2a2416",
        box_shadow=False,
    )

    st.markdown("<br><br>", unsafe_allow_html=True)
    render_summary(analysis.get("summary", ""))
    st.markdown("<br><br>", unsafe_allow_html=True)
    render_skills_section(
        matched_skills=analysis.get("matched_skills", []),
        missing_skills=analysis.get("missing_skills", []),
        bonus_skills=analysis.get("bonus_skills", []),
    )
    st.markdown("<br><br>", unsafe_allow_html=True)
    render_resume_tips(analysis.get("resume_tips", []))
    st.markdown("<br><br>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        job  = result.get("job", {})
        if st.button("Apply for this job →", use_container_width=True, type="primary"):
            st.session_state.prefill_job = {
                "url":     st.session_state.get("analyze_url", "") or "",
                "title":   job.get("title", ""),
                "company": job.get("company", ""),
            }
            # Inject JS to click the Apply tab (3rd tab)
            st.markdown("""
            <script>
            (function() {
                const tabs = window.parent.document.querySelectorAll('button[data-baseweb="tab"]');
                if (tabs.length >= 3) { tabs[2].click(); }
            })();
            </script>
            """, unsafe_allow_html=True)
            st.rerun()
    with col2:
        pdf_bytes = _generate_pdf_report(
            result,
            job_url=st.session_state.get("analyze_url")
        )
        job_title_slug = result.get("job", {}).get("title", "report").replace(" ", "_")[:30]
        st.download_button(
            "⇓ Download PDF Report",
            data=pdf_bytes,
            file_name=f"analysis_{job_title_slug}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )


def _render_recommendations(result: dict):
    recommendations = result.get("recommendation", [])
    search_query = result.get("search_query", "")
    total_found = result.get("total_jobs_found", 0)

    st.markdown("---")
    st.markdown(f"""
    <div style="margin-bottom: 20px;">
        <h2 class="grad-text" style="font-size: 28px; font-weight: 700; letter-spacing: -0.5px; margin-bottom: 8px; font-family:'Playfair Display',serif;">Top matches for your resume</h2>
        <p style="color: #6a6050; font-size: 14px; margin: 0; font-family:'DM Sans',sans-serif;">Searched for <strong style="color: #e2c97e; font-family:'JetBrains Mono',monospace; background:rgba(201,168,76,0.10); padding:2px 8px; border-radius:6px; font-size:12.5px;">"{search_query}"</strong> — <span style="color:#c9a84c; font-weight:600;">{total_found}</span> jobs analyzed</p>
    </div>
    """, unsafe_allow_html=True)

    if not recommendations:
        st.warning("No recommendations found. Try different preferences.")
        return

    for rec in recommendations:
        job = rec.get("job", {})
        render_job_card(
            job=job,
            rank=rec.get("rank", 0),
            match_percentage=rec.get("match_percentage", 0),
            match_label=rec.get("match_label", ""),
            match_color=rec.get("match_color", "gray"),
        )
        with st.expander(f"Details — {job.get('title', '')}"):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Matched skills**")
                matched = rec.get("matched_skills", [])
                if matched:
                    st.markdown(" ".join([f"`{s}`" for s in matched]))
            with col2:
                st.markdown("**Missing skills**")
                for skill in rec.get("missing_skills", []):
                    name = skill.get("skill", "") \
                        if isinstance(skill, dict) else skill.skill
                    st.markdown(f"- {name}")
            st.markdown(f"**Summary:** {rec.get('summary', '')}")
            if job.get("url"):
                col1, col2 = st.columns(2)
                with col1:
                    st.link_button(
                        "View job posting →",
                        url=job.get("url", ""),
                        use_container_width=True,
                    )
                with col2:
                    if st.button(
                        "Pre-fill application →",
                        key=f"apply_{rec.get('rank', 0)}",
                        use_container_width=True,
                        type="primary",
                    ):
                        # Store job details so Apply tab can read them
                        st.session_state.prefill_job = {
                            "url":     job.get("url", ""),
                            "title":   job.get("title", ""),
                            "company": job.get("company", ""),
                        }
                        # Inject JS to programmatically click the Apply tab (3rd tab)
                        st.markdown("""
                        <script>
                        (function() {
                            const tabs = window.parent.document.querySelectorAll(
                                'button[data-baseweb="tab"]'
                            );
                            if (tabs.length >= 3) { tabs[2].click(); }
                        })();
                        </script>
                        """, unsafe_allow_html=True)
                        st.rerun()


def _render_apply_results(result: dict):
    fields_filled = result.get("fields_filled", [])
    fields_failed = result.get("fields_failed", [])

    st.markdown("---")
    st.markdown("""<h2 class="grad-text" style="font-size: 28px; font-weight: 700; letter-spacing: -0.5px; margin: 0 0 8px 0; font-family:'Playfair Display',serif;">Application pre-filled</h2>""", unsafe_allow_html=True)

    st.success(f"✓ {result.get('message', 'Form pre-filled successfully.')}")

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Fields filled automatically**")
        for field in fields_filled:
            st.markdown(f"✓ {field.replace('_', ' ').title()}")
        if not fields_filled:
            st.info("No fields were auto-filled.")
    with col2:
        st.markdown("**Fields that need your attention**")
        for field in fields_failed:
            st.markdown(f"⚠ {field.replace('_', ' ').title()}")
        if not fields_failed:
            st.success("All fields filled!")

    st.markdown("<br>", unsafe_allow_html=True)

    cover_letter = result.get("application_data", {}).get("cover_letter", "")
    if cover_letter:
        with st.expander("View generated cover letter"):
            st.markdown(f"""
            <div style="background: rgba(18,16,10,0.82); backdrop-filter: blur(14px); border: 1px solid rgba(201,168,76,0.12); border-radius: 12px; padding: 24px; color: #c8bfaa; line-height: 1.9; font-size: 15px; white-space: pre-wrap; font-family:'DM Sans',sans-serif;">{cover_letter}</div>
            """, unsafe_allow_html=True)
            st.download_button(
                "Download cover letter",
                data=cover_letter,
                file_name="cover_letter.txt",
                mime="text/plain",
                use_container_width=True,
            )


if __name__ == "__main__":
    main()