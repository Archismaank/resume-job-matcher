
# ui/auth/login.py

import streamlit as st
import requests

AUTH_API = "http://localhost:8000/api/v1/auth"


# ─── CSS specific to the auth page ────────────────────────────────────────────

def _inject_auth_css():
    st.markdown("""
    <style>
    .auth-card {
        background: rgba(18, 16, 10, 0.82);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(201,168,76,0.14);
        border-radius: 20px;
        padding: 40px 36px;
        box-shadow: 0 32px 80px -24px rgba(0,0,0,0.7), 0 0 0 1px rgba(201,168,76,0.06);
    }
    .auth-brand-mark {
        text-align: center;
        padding: 48px 0 36px 0;
    }
    .auth-brand-mark .icon {
        font-size: 28px;
        color: #c9a84c;
        display: block;
        margin-bottom: 14px;
        letter-spacing: 6px;
    }
    .auth-footer-text {
        text-align: center;
        color: #4a4030;
        font-size: 13px;
        font-family: 'DM Sans', sans-serif;
        margin-top: 24px;
    }
    .field-label {
        color: #8a8070;
        font-size: 11.5px;
        font-family: 'DM Sans', sans-serif;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        margin-bottom: 6px;
        display: block;
    }
    /* Hide Streamlit's auto-generated sidebar nav and sidebar entirely */
    [data-testid="stSidebarNav"] { display: none !important; }
    section[data-testid="stSidebar"] { display: none !important; }
    </style>
    """, unsafe_allow_html=True)


# ─── Landing / Marketing Page ─────────────────────────────────────────────────

def render_landing_page():
    """
    Renders a marketing landing page visible before login.
    Shows feature showcase, stats, and CTA to get started.
    """
    _inject_auth_css()

    # ── Hero Section ──────────────────────────────────────────────────────────
    st.markdown("""
    <div style="text-align:center; padding:60px 20px 20px 20px;">
        <div style="display:inline-block; padding:6px 18px; border-radius:999px;
            background:rgba(201,168,76,0.08); border:1px solid rgba(201,168,76,0.28);
            color:#e2c97e; font-family:'DM Sans',sans-serif; font-size:11px;
            font-weight:600; letter-spacing:2.5px; text-transform:uppercase;
            margin-bottom:22px;">
            ✦ &nbsp; AI-Powered Career Tool &nbsp; ✦
        </div>
        <h1 class="grad-text" style="font-size:64px; font-weight:800; margin:0 0 18px 0;
            line-height:1.05; letter-spacing:-2px; font-family:'Playfair Display',serif;">
            Land Your Dream Job<br>With AI Precision
        </h1>
        <p style="font-size:19px; color:#6a6050; max-width:640px; margin:0 auto 32px auto;
            line-height:1.8; font-family:'DM Sans',sans-serif;">
            Upload your resume, get an AI match score against any job posting,
            and discover the best-fitting positions across
            <b style="color:#c9a84c;">Naukri</b>,
            <b style="color:#c9a84c;">Adzuna</b>, and
            <b style="color:#c9a84c;">JSearch</b> — all in seconds.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ── CTA Buttons ───────────────────────────────────────────────────────────
    _, btn_col1, btn_col2, _ = st.columns([1.5, 1, 1, 1.5])
    with btn_col1:
        if st.button("Get Started →", use_container_width=True, type="primary"):
            st.session_state.show_auth_form = True
            st.session_state.auth_mode = "signup"
            st.rerun()
    with btn_col2:
        if st.button("Sign In", use_container_width=True):
            st.session_state.show_auth_form = True
            st.session_state.auth_mode = "login"
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Stats Bar ─────────────────────────────────────────────────────────────
    s1, s2, s3, s4 = st.columns(4)
    stats = [
        ("3", "Job Portals", "Searched simultaneously"),
        ("< 30s", "Analysis Time", "Per resume-job pair"),
        ("100%", "Free", "No credit card required"),
        ("∞", "Unlimited", "Analyses & searches"),
    ]
    for col, (value, label, sub) in zip([s1, s2, s3, s4], stats):
        with col:
            st.markdown(f"""
            <div style="text-align:center; padding:24px 12px; background:rgba(18,16,10,0.72);
                backdrop-filter:blur(14px); border:1px solid rgba(201,168,76,0.10);
                border-radius:16px;">
                <div style="font-size:28px; font-weight:800; color:#c9a84c;
                    font-family:'Playfair Display',serif;">{value}</div>
                <div style="font-size:13px; font-weight:600; color:#a89880;
                    font-family:'DM Sans',sans-serif; margin-top:4px;">{label}</div>
                <div style="font-size:11px; color:#5a5040;
                    font-family:'DM Sans',sans-serif; margin-top:2px;">{sub}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)

    # ── Feature Cards ─────────────────────────────────────────────────────────
    st.markdown("""
    <div style="text-align:center; margin-bottom:28px;">
        <h2 class="grad-text" style="font-size:36px; font-weight:700;
            font-family:'Playfair Display',serif; margin:0;">
            Everything You Need
        </h2>
        <p style="color:#5a5040; font-size:15px; font-family:'DM Sans',sans-serif;
            margin-top:8px;">
            Three powerful features to supercharge your job search
        </p>
    </div>
    """, unsafe_allow_html=True)

    f1, f2, f3 = st.columns(3, gap="medium")
    features = [
        ("🔍", "Smart Analysis",
         "Upload your resume and paste any job URL or description. "
         "Get a detailed match score, skill gaps, experience fit, and actionable resume tips."),
        ("💼", "Job Discovery",
         "We search Naukri, Adzuna, and JSearch simultaneously, "
         "then rank every result by how well it matches your unique profile."),
        ("📄", "PDF Reports",
         "Download professional analysis reports with match scores, "
         "skill breakdowns, and improvement tips — perfect for tracking your progress."),
    ]
    for col, (icon, title, desc) in zip([f1, f2, f3], features):
        with col:
            st.markdown(f"""
            <div style="background:rgba(18,16,10,0.72); backdrop-filter:blur(14px);
                border:1px solid rgba(201,168,76,0.10); border-radius:16px;
                padding:28px 22px; min-height:240px;
                transition:transform 0.2s, border-color 0.2s, box-shadow 0.25s;"
                onmouseover="this.style.transform='translateY(-3px)';this.style.borderColor='rgba(201,168,76,0.42)';this.style.boxShadow='0 20px 40px -20px rgba(201,168,76,0.45)'"
                onmouseout="this.style.transform='';this.style.borderColor='rgba(201,168,76,0.10)';this.style.boxShadow=''">
                <div style="font-size:36px; margin-bottom:14px;
                    filter:drop-shadow(0 4px 14px rgba(201,168,76,0.32));">{icon}</div>
                <div style="font-size:17px; font-weight:700; color:#e2c97e;
                    font-family:'DM Sans',sans-serif; margin-bottom:10px;">{title}</div>
                <div style="font-size:14px; color:#8a8070; line-height:1.7;
                    font-family:'DM Sans',sans-serif;">{desc}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)

    # ── How It Works ──────────────────────────────────────────────────────────
    st.markdown("""
    <div style="text-align:center; margin-bottom:28px;">
        <h2 class="grad-text" style="font-size:36px; font-weight:700;
            font-family:'Playfair Display',serif; margin:0;">
            How It Works
        </h2>
        <p style="color:#5a5040; font-size:15px; font-family:'DM Sans',sans-serif;
            margin-top:8px;">
            From upload to insight in four simple steps
        </p>
    </div>
    """, unsafe_allow_html=True)

    h1, h2, h3, h4 = st.columns(4)
    steps = [
        ("01", "📄", "Upload Resume", "PDF or DOCX — we extract everything with AI"),
        ("02", "🧠", "AI Extracts Skills", "GPT-4o-mini identifies your skills, experience & projects"),
        ("03", "🔗", "Match or Search", "Compare against a specific job or search across 3 portals"),
        ("04", "📊", "Get Results", "Match scores, skill gaps, tips & downloadable PDF reports"),
    ]
    for col, (num, icon, title, desc) in zip([h1, h2, h3, h4], steps):
        with col:
            st.markdown(f"""
            <div style="position:relative; background:rgba(18,16,10,0.72);
                backdrop-filter:blur(14px); border:1px solid rgba(201,168,76,0.10);
                border-radius:16px; padding:24px 16px; text-align:center; min-height:180px;">
                <div style="position:absolute; top:10px; left:14px; font-size:11px;
                    font-weight:800; color:rgba(201,168,76,0.3); font-family:'DM Sans',sans-serif;
                    letter-spacing:1px;">{num}</div>
                <div style="font-size:30px; margin-bottom:12px;
                    filter:drop-shadow(0 4px 14px rgba(201,168,76,0.32));">{icon}</div>
                <div style="font-size:14px; font-weight:700; color:#e2c97e;
                    font-family:'DM Sans',sans-serif; margin-bottom:6px;">{title}</div>
                <div style="font-size:12.5px; color:#6a6050; line-height:1.6;
                    font-family:'DM Sans',sans-serif;">{desc}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)

    # ── Bottom CTA ────────────────────────────────────────────────────────────
    st.markdown("""
    <div style="text-align:center; padding:40px 20px; background:rgba(18,16,10,0.72);
        backdrop-filter:blur(14px); border:1px solid rgba(201,168,76,0.10);
        border-radius:20px; margin-bottom:20px;">
        <h2 class="grad-text" style="font-size:32px; font-weight:700;
            font-family:'Playfair Display',serif; margin:0 0 10px 0;">
            Ready to find your perfect match?
        </h2>
        <p style="color:#5a5040; font-size:15px; font-family:'DM Sans',sans-serif;
            margin:0 0 24px 0;">
            Create a free account and start analyzing in under 30 seconds.
        </p>
    </div>
    """, unsafe_allow_html=True)

    _, cta_col, _ = st.columns([1.5, 1, 1.5])
    with cta_col:
        if st.button("Create Free Account →", use_container_width=True, type="primary", key="cta_bottom"):
            st.session_state.show_auth_form = True
            st.session_state.auth_mode = "signup"
            st.rerun()

    # ── Footer ────────────────────────────────────────────────────────────────
    st.markdown("""
    <div style="text-align:center; padding:30px 0 10px 0; color:#3a3020;
        font-size:12px; font-family:'DM Sans',sans-serif;">
        Built with ✦ FastAPI · Streamlit · OpenAI GPT-4o-mini · Playwright
    </div>
    """, unsafe_allow_html=True)


# ─── Main render function ──────────────────────────────────────────────────────

def render_login_page():
    """
    Renders the full-page login / signup UI.
    Shows a centered auth card with a toggle between Sign In and Create Account.
    On success, stores the JWT token in session state and reruns to show the app.
    """
    _inject_auth_css()

    # Back to landing page
    if st.button("← Back", key="back_to_landing"):
        st.session_state.show_auth_form = False
        st.rerun()

    # Brand header — centered above the card
    st.markdown("""
    <div class="auth-brand-mark">
        <span class="icon">✦ ✦ ✦</span>
        <h1 class="grad-text" style="font-size:42px; font-weight:800; margin:0 0 10px 0;
            font-family:'Playfair Display',serif; line-height:1.1;">
            Resume Job Matcher
        </h1>
        <p style="color:#5a5040; font-size:15px; font-family:'DM Sans',sans-serif;
            font-weight:400; margin:0;">
            AI-powered career matching — sign in to get started
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Narrow centered column for the form card
    _, center, _ = st.columns([1, 1.4, 1])

    with center:

        # ── Mode toggle (Sign In / Create Account) ──────────────────────────
        if "auth_mode" not in st.session_state:
            st.session_state.auth_mode = "login"

        if st.session_state.auth_mode in ["login", "signup"]:
            tab_col1, tab_col2 = st.columns(2, gap="small")
            with tab_col1:
                login_type = "primary" if st.session_state.auth_mode == "login" else "secondary"
                if st.button("Sign In", use_container_width=True, type=login_type, key="btn_login_tab"):
                    st.session_state.auth_mode = "login"
                    st.session_state.pop("auth_error", None)
                    st.session_state.pop("auth_success", None)
                    st.rerun()
            with tab_col2:
                signup_type = "primary" if st.session_state.auth_mode == "signup" else "secondary"
                if st.button("Create Account", use_container_width=True, type=signup_type, key="btn_signup_tab"):
                    st.session_state.auth_mode = "signup"
                    st.session_state.pop("auth_error", None)
                    st.session_state.pop("auth_success", None)
                    st.rerun()

            st.markdown("<br>", unsafe_allow_html=True)

        # ── Auth card ────────────────────────────────────────────────────────
        st.markdown('<div class="auth-card">', unsafe_allow_html=True)

        # Show any error from previous attempt
        if st.session_state.get("auth_error"):
            st.error(st.session_state.auth_error)
            st.session_state.pop("auth_error")

        if st.session_state.get("auth_success"):
            st.success(st.session_state.auth_success)
            st.session_state.pop("auth_success")

        if st.session_state.auth_mode == "login":
            _render_login_form()
        elif st.session_state.auth_mode == "signup":
            _render_signup_form()
        elif st.session_state.auth_mode == "forgot_password":
            _render_forgot_password_form()
        elif st.session_state.auth_mode == "reset_password":
            _render_reset_password_form()

        st.markdown('</div>', unsafe_allow_html=True)

        # Footer note
        st.markdown("""
        <p class="auth-footer-text">
            Your resume data is never stored permanently. &nbsp;✦&nbsp; Powered by OpenAI.
        </p>
        """, unsafe_allow_html=True)


# ─── Login Form ───────────────────────────────────────────────────────────────

def _render_login_form():
    st.markdown("""
    <h2 style="font-family:'Playfair Display',serif; font-size:22px; font-weight:700;
               color:#f0ebe0; margin:0 0 6px 0;">Welcome back</h2>
    <p style="color:#5a5040; font-size:13.5px; font-family:'DM Sans',sans-serif; margin:0 0 24px 0;">
        Sign in to your account to continue.
    </p>
    """, unsafe_allow_html=True)

    with st.form("login_form", clear_on_submit=False):
        st.markdown('<span class="field-label">Email address</span>', unsafe_allow_html=True)
        email = st.text_input(
            "email",
            placeholder="you@example.com",
            label_visibility="collapsed",
        )

        st.markdown('<span class="field-label">Password</span>', unsafe_allow_html=True)
        password = st.text_input(
            "password",
            type="password",
            placeholder="Your password",
            label_visibility="collapsed",
        )

        st.markdown("<br>", unsafe_allow_html=True)
        submitted = st.form_submit_button(
            "Sign In →",
            use_container_width=True,
            type="primary",
        )

    if submitted:
        if not email or not password:
            st.session_state.auth_error = "Please fill in all fields."
            st.rerun()
        else:
            _handle_login(email.strip(), password)

    st.markdown("<div style='text-align: center; margin-top: 10px;'>", unsafe_allow_html=True)
    if st.button("Forgot your password?", type="tertiary", use_container_width=True):
        st.session_state.auth_mode = "forgot_password"
        st.session_state.pop("auth_error", None)
        st.session_state.pop("auth_success", None)
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


# ─── Signup Form ──────────────────────────────────────────────────────────────

def _render_signup_form():
    st.markdown("""
    <h2 style="font-family:'Playfair Display',serif; font-size:22px; font-weight:700;
               color:#f0ebe0; margin:0 0 6px 0;">Create your account</h2>
    <p style="color:#5a5040; font-size:13.5px; font-family:'DM Sans',sans-serif; margin:0 0 24px 0;">
        Free forever. No credit card required.
    </p>
    """, unsafe_allow_html=True)

    with st.form("signup_form", clear_on_submit=False):
        st.markdown('<span class="field-label">Full name</span>', unsafe_allow_html=True)
        name = st.text_input(
            "name",
            placeholder="Jane Smith",
            label_visibility="collapsed",
        )

        st.markdown('<span class="field-label">Email address</span>', unsafe_allow_html=True)
        email = st.text_input(
            "email",
            placeholder="you@example.com",
            label_visibility="collapsed",
        )

        st.markdown('<span class="field-label">Password</span>', unsafe_allow_html=True)
        password = st.text_input(
            "password",
            type="password",
            placeholder="At least 8 characters",
            label_visibility="collapsed",
        )

        st.markdown('<span class="field-label">Confirm password</span>', unsafe_allow_html=True)
        confirm = st.text_input(
            "confirm_password",
            type="password",
            placeholder="Repeat your password",
            label_visibility="collapsed",
        )

        st.markdown("<br>", unsafe_allow_html=True)
        submitted = st.form_submit_button(
            "Create Account →",
            use_container_width=True,
            type="primary",
        )

    if submitted:
        error = _validate_signup(name, email, password, confirm)
        if error:
            st.session_state.auth_error = error
            st.rerun()
        else:
            _handle_signup(name.strip(), email.strip(), password)


# ─── Forgot Password Form ─────────────────────────────────────────────────────

def _render_forgot_password_form():
    st.markdown("""
    <h2 style="font-family:'Playfair Display',serif; font-size:22px; font-weight:700;
               color:#f0ebe0; margin:0 0 6px 0;">Reset Password</h2>
    <p style="color:#5a5040; font-size:13.5px; font-family:'DM Sans',sans-serif; margin:0 0 24px 0;">
        Enter your email and we'll send you a link to reset your password.
    </p>
    """, unsafe_allow_html=True)

    with st.form("forgot_password_form", clear_on_submit=False):
        st.markdown('<span class="field-label">Email address</span>', unsafe_allow_html=True)
        email = st.text_input(
            "email",
            placeholder="you@example.com",
            label_visibility="collapsed",
        )

        st.markdown("<br>", unsafe_allow_html=True)
        submitted = st.form_submit_button(
            "Send Reset Link →",
            use_container_width=True,
            type="primary",
        )

    if submitted:
        if not email:
            st.session_state.auth_error = "Please enter your email address."
            st.rerun()
        else:
            _handle_forgot_password(email.strip())

    st.markdown("<div style='text-align: center; margin-top: 10px;'>", unsafe_allow_html=True)
    if st.button("Back to Login", type="tertiary", use_container_width=True):
        st.session_state.auth_mode = "login"
        st.session_state.pop("auth_error", None)
        st.session_state.pop("auth_success", None)
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


# ─── Reset Password Form ──────────────────────────────────────────────────────

def _render_reset_password_form():
    st.markdown("""
    <h2 style="font-family:'Playfair Display',serif; font-size:22px; font-weight:700;
               color:#f0ebe0; margin:0 0 6px 0;">Set New Password</h2>
    <p style="color:#5a5040; font-size:13.5px; font-family:'DM Sans',sans-serif; margin:0 0 24px 0;">
        Please enter your new password below.
    </p>
    """, unsafe_allow_html=True)

    with st.form("reset_password_form", clear_on_submit=False):
        st.markdown('<span class="field-label">New Password</span>', unsafe_allow_html=True)
        password = st.text_input(
            "new_password",
            type="password",
            placeholder="At least 8 characters",
            label_visibility="collapsed",
        )
        
        st.markdown('<span class="field-label">Confirm New Password</span>', unsafe_allow_html=True)
        confirm = st.text_input(
            "confirm_new_password",
            type="password",
            placeholder="Repeat your new password",
            label_visibility="collapsed",
        )

        st.markdown("<br>", unsafe_allow_html=True)
        submitted = st.form_submit_button(
            "Update Password →",
            use_container_width=True,
            type="primary",
        )

    if submitted:
        if not password or not confirm:
            st.session_state.auth_error = "Please fill in all fields."
            st.rerun()
        elif len(password) < 8:
            st.session_state.auth_error = "Password must be at least 8 characters."
            st.rerun()
        elif password != confirm:
            st.session_state.auth_error = "Passwords do not match."
            st.rerun()
        else:
            token = st.session_state.get("reset_token")
            if token:
                _handle_reset_password(token, password)
            else:
                st.session_state.auth_error = "Reset token missing. Please click the link in your email again."
                st.rerun()

    st.markdown("<div style='text-align: center; margin-top: 10px;'>", unsafe_allow_html=True)
    if st.button("Cancel", type="tertiary", use_container_width=True):
        st.session_state.auth_mode = "login"
        st.session_state.pop("auth_error", None)
        st.session_state.pop("auth_success", None)
        st.session_state.pop("reset_token", None)
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


# ─── Validation ───────────────────────────────────────────────────────────────

def _validate_signup(name, email, password, confirm) -> str | None:
    """Returns an error string if validation fails, None if OK."""
    if not name or not email or not password or not confirm:
        return "Please fill in all fields."
    if len(password) < 8:
        return "Password must be at least 8 characters."
    if password != confirm:
        return "Passwords do not match."
    if "@" not in email or "." not in email:
        return "Please enter a valid email address."
    return None


# ─── API Calls ────────────────────────────────────────────────────────────────

def _get_error_detail(response, fallback: str) -> str:
    """Safely extracts the error detail from a response body.
    Falls back gracefully if the body is empty or not valid JSON."""
    try:
        return response.json().get("detail", fallback)
    except Exception:
        # Body was empty, HTML, or not valid JSON
        return f"{fallback} (HTTP {response.status_code})"

def _handle_login(email: str, password: str):
    """Calls POST /auth/login, stores token on success."""
    try:
        response = requests.post(
            f"{AUTH_API}/login",
            json={"email": email, "password": password},
            timeout=15,
        )
        if response.status_code == 200:
            data = response.json()
            _store_session(data)
            st.session_state.pop("is_unverified", None)
            st.rerun()
        elif response.status_code == 403:
            detail = _get_error_detail(response, "Login failed.")
            if detail == "EMAIL_NOT_VERIFIED":
                # Log them in but flag as unverified — they can still use the app
                # but will see the banner
                st.session_state.auth_error = (
                    "📧 Please verify your email address. "
                    "Check your inbox for the verification link."
                )
                st.session_state.is_unverified = True
                # Try to log them in anyway without verification check
                # Actually just show error — they can't log in until verified
            else:
                st.session_state.auth_error = detail
            st.rerun()
        else:
            st.session_state.auth_error = _get_error_detail(response, "Login failed.")
            st.rerun()
    except requests.exceptions.ConnectionError:
        st.session_state.auth_error = "Cannot reach the backend. Is the server running?"
        st.rerun()
    except Exception as e:
        st.session_state.auth_error = f"Something went wrong: {e}"
        st.rerun()


def _handle_signup(name: str, email: str, password: str):
    """Calls POST /auth/signup, stores token on success."""
    try:
        response = requests.post(
            f"{AUTH_API}/signup",
            json={"name": name, "email": email, "password": password},
            timeout=15,
        )
        if response.status_code == 201:
            _store_session(response.json())
            st.rerun()
        else:
            st.session_state.auth_error = _get_error_detail(response, "Signup failed.")
            st.rerun()
    except requests.exceptions.ConnectionError:
        st.session_state.auth_error = "Cannot reach the backend. Is the server running?"
        st.rerun()
    except Exception as e:
        st.session_state.auth_error = f"Something went wrong: {e}"
        st.rerun()


def _handle_forgot_password(email: str):
    """Calls POST /auth/forgot-password."""
    try:
        response = requests.post(
            f"{AUTH_API}/forgot-password",
            json={"email": email},
            timeout=15,
        )
        if response.status_code == 200:
            st.session_state.auth_success = response.json().get("message", "Reset link sent.")
            st.session_state.auth_mode = "login"
            st.rerun()
        else:
            st.session_state.auth_error = _get_error_detail(response, "Failed to send reset link.")
            st.rerun()
    except requests.exceptions.ConnectionError:
        st.session_state.auth_error = "Cannot reach the backend. Is the server running?"
        st.rerun()
    except Exception as e:
        st.session_state.auth_error = f"Something went wrong: {e}"
        st.rerun()


def _handle_reset_password(token: str, new_password: str):
    """Calls POST /auth/reset-password."""
    try:
        response = requests.post(
            f"{AUTH_API}/reset-password",
            json={"token": token, "new_password": new_password},
            timeout=15,
        )
        if response.status_code == 200:
            st.session_state.auth_success = response.json().get("message", "Password reset successfully.")
            st.session_state.auth_mode = "login"
            st.session_state.pop("reset_token", None)
            st.rerun()
        else:
            st.session_state.auth_error = _get_error_detail(response, "Failed to reset password.")
            st.rerun()
    except requests.exceptions.ConnectionError:
        st.session_state.auth_error = "Cannot reach the backend. Is the server running?"
        st.rerun()
    except Exception as e:
        st.session_state.auth_error = f"Something went wrong: {e}"
        st.rerun()


# ─── Session Helpers ──────────────────────────────────────────────────────────

def _store_session(data: dict):
    """Saves auth response into Streamlit session state and persists token
    in query params so a page refresh does not log the user out."""
    st.session_state.access_token = data["access_token"]
    st.session_state.user_id      = data["user_id"]
    st.session_state.user_name    = data["name"]
    st.session_state.user_email   = data["email"]
    # Persist token in URL query param — survives browser refresh
    st.query_params["token"] = data["access_token"]


def logout():
    """Clears all auth-related and result session state keys."""
    for key in [
        "access_token", "user_id", "user_name", "user_email",
        "resume_file", "resume_name",
        "analyze_result", "recommend_result",
        "analyze_url", "url_result_cache",
        "show_auth_form",
    ]:
        st.session_state.pop(key, None)
    # Remove token from URL so refresh doesn't restore the session
    st.query_params.clear()
