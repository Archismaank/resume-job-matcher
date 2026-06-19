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


# ─── Main render function ──────────────────────────────────────────────────────

def render_login_page():
    """
    Renders the full-page login / signup UI.
    Shows a centered auth card with a toggle between Sign In and Create Account.
    On success, stores the JWT token in session state and reruns to show the app.
    """
    _inject_auth_css()

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

        tab_col1, tab_col2 = st.columns(2, gap="small")
        with tab_col1:
            login_type = "primary" if st.session_state.auth_mode == "login" else "secondary"
            if st.button("Sign In", use_container_width=True, type=login_type, key="btn_login_tab"):
                st.session_state.auth_mode = "login"
                st.session_state.pop("auth_error", None)
                st.rerun()
        with tab_col2:
            signup_type = "primary" if st.session_state.auth_mode == "signup" else "secondary"
            if st.button("Create Account", use_container_width=True, type=signup_type, key="btn_signup_tab"):
                st.session_state.auth_mode = "signup"
                st.session_state.pop("auth_error", None)
                st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Auth card ────────────────────────────────────────────────────────
        st.markdown('<div class="auth-card">', unsafe_allow_html=True)

        # Show any error from previous attempt
        if st.session_state.get("auth_error"):
            st.error(st.session_state.auth_error)
            st.session_state.pop("auth_error")

        if st.session_state.auth_mode == "login":
            _render_login_form()
        else:
            _render_signup_form()

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
            _store_session(response.json())
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
        "analyze_result", "recommend_result", "prefill_job",
    ]:
        st.session_state.pop(key, None)
    # Remove token from URL so refresh doesn't restore the session
    st.query_params.clear()
