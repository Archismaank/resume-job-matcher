# ui/components.py

import streamlit as st


def set_page_config():
    """Sets the page configuration and custom CSS."""
    st.set_page_config(
        page_title="Resume Job Matcher",
        page_icon="✦",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    _inject_css()


def _inject_css():
    st.markdown("""
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,500;0,600;0,700;0,800;1,500;1,700&family=DM+Sans:opsz,wght@9..40,300;9..40,400;9..40,500;9..40,600;9..40,700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }
    html, body, [class*="css"], .stApp { font-family: 'DM Sans', -apple-system, BlinkMacSystemFont, sans-serif; -webkit-font-smoothing: antialiased; }
    .stApp { background: radial-gradient(1400px 700px at 5% -5%, rgba(201,168,76,0.09), transparent 55%), radial-gradient(1000px 500px at 95% 5%, rgba(160,120,48,0.06), transparent 55%), radial-gradient(900px 600px at 50% 105%, rgba(100,78,28,0.08), transparent 55%), #080705; color: #f0ebe0; }
    /* Hide sidebar and its nav entirely — this app uses a top bar instead */
    section[data-testid="stSidebar"] { display: none !important; }
    [data-testid="stSidebarNav"] { display: none !important; }
    button[data-testid="stSidebarToggle"] { display: none !important; }
    .main { background: transparent; }
    .block-container { padding-top: 1rem !important; max-width: 1180px; }
    h1, h2, h3, h4 { font-family: 'Playfair Display', Georgia, serif !important; letter-spacing: -0.01em; }
    .stTabs [data-baseweb="tab-list"] { background: rgba(18,16,10,0.70); backdrop-filter: blur(14px); -webkit-backdrop-filter: blur(14px); border: 1px solid rgba(201,168,76,0.12); border-radius: 14px; gap: 6px; padding: 6px; }
    .stTabs [data-baseweb="tab"] { background: transparent; color: #5a5040; font-family: 'DM Sans', sans-serif; font-size: 14px; font-weight: 600; padding: 12px 22px; border-radius: 10px; border-bottom: none; transition: color .2s ease, background .2s ease; }
    .stTabs [data-baseweb="tab"]:hover { color: #f0ebe0; }
    .stTabs [aria-selected="true"] { color: #080705 !important; background: linear-gradient(135deg, #c9a84c 0%, #e8d080 50%, #b08030 100%) !important; border-bottom: none !important; box-shadow: 0 8px 24px -10px rgba(201,168,76,0.55); }
    .stTextInput input, .stTextArea textarea { background: rgba(18,16,10,0.80) !important; border: 1px solid rgba(201,168,76,0.15) !important; border-radius: 12px !important; color: #f0ebe0 !important; font-family: 'DM Sans', sans-serif; font-size: 15px; padding: 12px 16px !important; transition: all .2s ease; }
    .stTextInput input:focus, .stTextArea textarea:focus { border-color: #c9a84c !important; box-shadow: 0 0 0 3px rgba(201,168,76,0.12), 0 0 24px -8px rgba(201,168,76,0.30) !important; outline: none !important; }
    [data-testid="stFileUploader"] { border: 1.5px dashed rgba(201,168,76,0.32); border-radius: 14px; padding: 14px; background: linear-gradient(135deg, rgba(201,168,76,0.05), rgba(160,120,48,0.03)); transition: all .25s ease; }
    [data-testid="stFileUploader"]:hover { border-color: #c9a84c; background: linear-gradient(135deg, rgba(201,168,76,0.10), rgba(160,120,48,0.06)); box-shadow: 0 0 32px -12px rgba(201,168,76,0.38); }
    .stButton button[kind="primary"] { background: linear-gradient(135deg, #c9a84c 0%, #e8d080 100%); background-size: 200% 200%; color: #080705; border: none; border-radius: 12px; font-family: 'DM Sans', sans-serif; font-size: 15px; font-weight: 700; padding: 12px 28px; letter-spacing: 0.3px; box-shadow: 0 10px 30px -10px rgba(201,168,76,0.50), inset 0 1px 0 rgba(255,255,255,0.28); transition: transform .15s ease, box-shadow .2s ease, background-position .4s ease; }
    .stButton button[kind="primary"]:hover { background-position: 100% 0%; transform: translateY(-1px); box-shadow: 0 18px 40px -12px rgba(201,168,76,0.65), inset 0 1px 0 rgba(255,255,255,0.32); }
    .stButton button[kind="primary"]:active { transform: translateY(0); }
    .stButton button[kind="secondary"], .stButton button:not([kind="primary"]) { background: rgba(201,168,76,0.06); color: #c9a84c; border: 1px solid rgba(201,168,76,0.24); border-radius: 12px; font-family: 'DM Sans', sans-serif; font-size: 15px; font-weight: 600; transition: all .2s ease; }
    .stButton button:not([kind="primary"]):hover { background: rgba(201,168,76,0.12); border-color: rgba(201,168,76,0.48); }
    [data-testid="metric-container"] { background: rgba(18,16,10,0.72) !important; backdrop-filter: blur(12px); border: 1px solid rgba(201,168,76,0.14) !important; border-radius: 14px !important; padding: 18px 22px !important; box-shadow: 0 8px 24px -16px rgba(0,0,0,0.6); }
    hr { border: none; height: 1px; background: linear-gradient(90deg, transparent, rgba(201,168,76,0.22), transparent); margin: 28px 0; }
    .skill-badge-matched { display: inline-block; background: linear-gradient(135deg, rgba(201,168,76,0.20), rgba(160,120,48,0.10)); color: #e2c97e; padding: 5px 12px; border-radius: 999px; margin: 3px; font-size: 13px; font-weight: 600; border: 1px solid rgba(201,168,76,0.32); box-shadow: 0 0 14px -6px rgba(201,168,76,0.32); }
    .skill-badge-missing { display: inline-block; background: linear-gradient(135deg, rgba(180,60,40,0.18), rgba(160,40,20,0.08)); color: #f0a898; padding: 5px 12px; border-radius: 999px; margin: 3px; font-size: 13px; font-weight: 600; border: 1px solid rgba(240,168,152,0.26); box-shadow: 0 0 14px -6px rgba(180,60,40,0.28); }
    .skill-badge-bonus { display: inline-block; background: linear-gradient(135deg, rgba(180,160,120,0.18), rgba(140,120,80,0.10)); color: #c8b898; padding: 5px 12px; border-radius: 999px; margin: 3px; font-size: 13px; font-weight: 600; border: 1px solid rgba(200,184,152,0.28); box-shadow: 0 0 14px -6px rgba(180,160,120,0.25); }
    .badge-must-have { background: rgba(180,60,40,0.15); color: #f0a898; padding: 2px 8px; border-radius: 6px; font-size: 10.5px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.6px; border: 1px solid rgba(240,168,152,0.24); }
    .badge-nice-to-have { background: rgba(201,168,76,0.14); color: #e2c97e; padding: 2px 8px; border-radius: 6px; font-size: 10.5px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.6px; border: 1px solid rgba(201,168,76,0.26); }
    .job-card { position: relative; background: rgba(18,16,10,0.80); backdrop-filter: blur(14px); -webkit-backdrop-filter: blur(14px); border: 1px solid rgba(201,168,76,0.10); border-radius: 16px; padding: 22px 26px; margin: 12px 0; overflow: hidden; transition: transform .2s ease, border-color .2s ease, box-shadow .25s ease; }
    .job-card::before { content: ""; position: absolute; inset: 0; border-radius: 16px; padding: 1px; background: linear-gradient(135deg, rgba(201,168,76,0.0), rgba(232,208,128,0.0)); -webkit-mask: linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0); -webkit-mask-composite: xor; mask-composite: exclude; pointer-events: none; transition: background .3s ease; }
    .job-card:hover { transform: translateY(-2px); border-color: transparent; box-shadow: 0 20px 48px -24px rgba(201,168,76,0.48); }
    .job-card:hover::before { background: linear-gradient(135deg, rgba(201,168,76,0.55), rgba(232,208,128,0.55)); }
    .tip-item { background: rgba(18,16,10,0.62); border-left: 3px solid; border-image: linear-gradient(180deg, #c9a84c, #8a6020) 1; padding: 12px 18px; margin: 8px 0; border-radius: 0 12px 12px 0; color: #c8bfaa; font-size: 14.5px; line-height: 1.7; transition: background .2s ease, transform .15s ease; }
    .tip-item:hover { background: rgba(18,16,10,0.90); transform: translateX(2px); }
    .stSelectbox [data-baseweb="select"] > div { background: rgba(18,16,10,0.80) !important; border: 1px solid rgba(201,168,76,0.14) !important; border-radius: 12px !important; }
    .streamlit-expanderHeader, [data-testid="stExpander"] summary { background: rgba(18,16,10,0.62) !important; border-radius: 12px !important; color: #8a8070 !important; font-family: 'DM Sans', sans-serif; font-size: 14px; font-weight: 600; border: 1px solid rgba(201,168,76,0.10) !important; }
    .source-badge { display: inline-block; background: rgba(18,16,10,0.78); backdrop-filter: blur(10px); color: #c8bfaa; padding: 10px 18px; border-radius: 999px; margin: 4px; font-family: 'DM Sans', sans-serif; font-size: 13.5px; font-weight: 600; border: 1px solid rgba(201,168,76,0.16); transition: all .2s ease; }
    .source-badge:hover { border-color: rgba(201,168,76,0.52); color: #f0ebe0; box-shadow: 0 0 24px -8px rgba(201,168,76,0.40); }
    .workflow-step { position: relative; background: rgba(18,16,10,0.72); backdrop-filter: blur(14px); border: 1px solid rgba(201,168,76,0.10); border-radius: 16px; padding: 20px 14px; text-align: center; font-family: 'DM Sans', sans-serif; font-weight: 600; color: #f0ebe0; min-height: 96px; display: flex; flex-direction: column; align-items: center; justify-content: center; transition: transform .2s ease, border-color .2s ease, box-shadow .25s ease; }
    .workflow-step:hover { transform: translateY(-3px); border-color: rgba(201,168,76,0.42); box-shadow: 0 20px 40px -20px rgba(201,168,76,0.45); }
    .resume-status-card { background: linear-gradient(135deg, rgba(201,168,76,0.07), rgba(160,120,48,0.04)), rgba(18,16,10,0.82); backdrop-filter: blur(14px); border: 1px solid rgba(201,168,76,0.22); border-radius: 16px; padding: 22px; margin-top: 14px; color: #f0ebe0; box-shadow: 0 10px 30px -16px rgba(201,168,76,0.32); }
    .resume-status-card h4 { margin-top: 0; color: #e2c97e; font-family: 'Playfair Display', serif; }
    .grad-text { background: linear-gradient(135deg, #e8d080 0%, #faf5e8 45%, #c9a84c 100%); background-size: 200% 200%; -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent; animation: shimmer 6s ease-in-out infinite; }
    @keyframes shimmer { 0%, 100% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } }
    div[data-baseweb="notification"] { border-radius: 12px !important; backdrop-filter: blur(10px); }
    ::-webkit-scrollbar { width: 10px; height: 10px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: linear-gradient(180deg, #c9a84c, #8a6020); border-radius: 999px; }
    </style>
    """, unsafe_allow_html=True)


def render_header():
    st.markdown(
        """
        <div style="text-align:center; padding:52px 20px 28px 20px;">
            <div style="display:inline-block; padding:6px 18px; border-radius:999px; background:rgba(201,168,76,0.08); border:1px solid rgba(201,168,76,0.28); color:#e2c97e; font-family:'DM Sans',sans-serif; font-size:11px; font-weight:600; letter-spacing:2.5px; text-transform:uppercase; margin-bottom:22px;">
                ✦ &nbsp; AI-Powered Career Matcher &nbsp; ✦
            </div>
            <h1 class="grad-text" style="font-size:68px; font-weight:800; margin:0 0 16px 0; line-height:1.05; letter-spacing:-2px; font-family:'Playfair Display',serif;">
                Resume Job Matcher
            </h1>
            <div style="font-size:18px; color:#6a6050; max-width:680px; margin:0 auto; line-height:1.8; font-weight:400; font-family:'DM Sans',sans-serif;">
                Discover curated jobs from <b style="color:#c9a84c; font-weight:600;">Naukri</b>, <b style="color:#c9a84c; font-weight:600;">Adzuna</b>, and <b style="color:#c9a84c; font-weight:600;">JSearch</b>,<br>ranked by AI to match your unique profile.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # source badges
    c1, c2, c3 = st.columns([1, 1, 1])

    with c1:
        st.markdown("""<div class="source-badge" style="text-align:center;">🇮🇳 &nbsp; Naukri</div>""", unsafe_allow_html=True)

    with c2:
        st.markdown("""<div class="source-badge" style="text-align:center;">🌍 &nbsp; Adzuna</div>""", unsafe_allow_html=True)

    with c3:
        st.markdown("""<div class="source-badge" style="text-align:center;">🔎 &nbsp; JSearch</div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    cols = st.columns(4)

    cards = [
        ("📄", "Upload Resume"),
        ("🧠", "AI Extracts Skills"),
        ("💼", "Find Matching Jobs"),
        ("🚀", "Apply Faster"),
    ]

    for col, (icon, text) in zip(cols, cards):
        with col:
            st.markdown(
                f"""
                <div class="workflow-step">
                    <div style="font-size:30px; margin-bottom:10px; filter:drop-shadow(0 4px 14px rgba(201,168,76,0.32));">{icon}</div>
                    <div style="font-size:14px; font-weight:600; color:#a89880; font-family:'DM Sans',sans-serif;">{text}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_global_resume_uploader():
    """
    Global resume uploader used across the app.
    Upload once and reuse everywhere.
    """

    st.markdown("### 📄 Your Resume")

    uploaded_file = st.file_uploader(
        "Upload Resume",
        type=["pdf", "docx"],
        label_visibility="collapsed",
        key="global_resume_upload"
    )

    if uploaded_file:
        # If a different resume is uploaded, clear all previous results + URL cache
        if uploaded_file.name != st.session_state.get("resume_name"):
            st.session_state.pop("analyze_result", None)
            st.session_state.pop("recommend_result", None)
            st.session_state.pop("prefill_job", None)
            st.session_state.pop("url_result_cache", None)
        st.session_state.resume_file = uploaded_file
        st.session_state.resume_name = uploaded_file.name

    if st.session_state.get("resume_file"):
        filename = st.session_state.get("resume_name", "")
        st.markdown(
            f"""
            <div class="resume-status-card">
                <h4 style="margin-top:0; font-size:16px;">✦ &nbsp; Resume Ready</h4>
                <p style="margin-bottom:10px; color:#8a8070; font-family:'DM Sans',sans-serif;">
                    <strong style="color:#f0ebe0;">File:</strong>&nbsp;
                    <span style="font-family:'JetBrains Mono',monospace; color:#e2c97e; font-size:13px;">{filename}</span>
                </p>
                <p style="margin:6px 0; color:#8a8070; font-family:'DM Sans',sans-serif;"><span style="color:#c9a84c;">✓</span>&nbsp; Uploaded Successfully</p>
                <p style="margin:6px 0; color:#8a8070; font-family:'DM Sans',sans-serif;"><span style="color:#c9a84c;">✓</span>&nbsp; Ready for Analysis</p>
                <p style="margin:6px 0; color:#8a8070; font-family:'DM Sans',sans-serif;"><span style="color:#c9a84c;">✓</span>&nbsp; Ready for Job Search</p>
                <p style="margin:6px 0; color:#8a8070; font-family:'DM Sans',sans-serif;"><span style="color:#c9a84c;">✓</span>&nbsp; Ready for Applications</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_match_score(percentage: float, label: str, color: str):
    """Renders the match score gauge."""
    import plotly.graph_objects as go

    # Determine color based on percentage — warm gold-toned spectrum
    if percentage >= 85:
        gauge_color = "#c9a84c"
    elif percentage >= 70:
        gauge_color = "#d4b86a"
    elif percentage >= 55:
        gauge_color = "#c08030"
    elif percentage >= 40:
        gauge_color = "#b06030"
    else:
        gauge_color = "#a04848"

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=percentage,
        title={"text": label, "font": {"size": 20, "color": "#a89880", "family": "Playfair Display"}},
        number={"suffix": "%", "font": {"size": 52, "color": gauge_color, "family": "Playfair Display"}},
        gauge={
            "axis": {
                "range": [0, 100],
                "tickcolor": "#3a3020",
                "tickfont": {"color": "#5a5040"},
            },
            "bar": {"color": gauge_color, "thickness": 0.28},
            "bgcolor": "rgba(201,168,76,0.04)",
            "bordercolor": "rgba(201,168,76,0.12)",
            "steps": [
                {"range": [0, 40],   "color": "rgba(160,64,64,0.10)"},
                {"range": [40, 70],  "color": "rgba(192,128,48,0.10)"},
                {"range": [70, 100], "color": "rgba(201,168,76,0.14)"},
            ],
            "threshold": {
                "line": {"color": gauge_color, "width": 4},
                "thickness": 0.78,
                "value": percentage,
            },
        }
    ))

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#f0ebe0", "family": "DM Sans"},
        height=320,
        margin={"t": 50, "b": 0, "l": 30, "r": 30},
    )

    st.plotly_chart(fig, use_container_width=True)


def render_skills_section(
    matched_skills: list,
    missing_skills: list,
    bonus_skills: list,
):
    """Renders matched, missing and bonus skills."""

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### ✦ Matched Skills")
        if matched_skills:
            badges = " ".join([
                f'<span class="skill-badge-matched">{s}</span>'
                for s in matched_skills
            ])
            st.markdown(badges, unsafe_allow_html=True)
        else:
            st.info("No matched skills found")

    with col2:
        st.markdown("### ✗ Missing Skills")
        if missing_skills:
            for skill in missing_skills:
                importance = skill.get("importance", "nice-to-have") \
                    if isinstance(skill, dict) \
                    else skill.importance
                skill_name = skill.get("skill", "") \
                    if isinstance(skill, dict) \
                    else skill.skill
                badge_class = "badge-must-have" \
                    if importance == "must-have" \
                    else "badge-nice-to-have"
                st.markdown(f"""
                <div style="margin: 6px 0;"><span class="skill-badge-missing">{skill_name}</span> <span class="{badge_class}">{importance}</span></div>
                """, unsafe_allow_html=True)
        else:
            st.success("No missing skills!")

    with col3:
        st.markdown("### ◈ Bonus Skills")
        if bonus_skills:
            badges = " ".join([
                f'<span class="skill-badge-bonus">{s}</span>'
                for s in bonus_skills
            ])
            st.markdown(badges, unsafe_allow_html=True)
        else:
            st.info("No bonus skills")


def render_resume_tips(tips: list):
    """Renders resume improvement tips."""
    st.markdown("### ✦ Resume Tips")
    for i, tip in enumerate(tips, 1):
        st.markdown(f"""<div class="tip-item"><strong style="color:#e2c97e; font-family:'Playfair Display',serif;">{i}.</strong> {tip}</div>""", unsafe_allow_html=True)


def render_summary(summary: str):
    """Renders the analysis summary."""
    st.markdown("### ✦ Summary")
    st.markdown(f"""
    <div style="background: rgba(18,16,10,0.80); backdrop-filter: blur(14px); border-radius: 16px; padding: 26px; border: 1px solid rgba(201,168,76,0.12); color: #c8bfaa; line-height: 1.9; font-size: 15.5px; box-shadow: 0 10px 30px -20px rgba(0,0,0,0.6); font-family:'DM Sans',sans-serif;">
        {summary}
    </div>
    """, unsafe_allow_html=True)


def render_job_card(job: dict, rank: int, match_percentage: float,
                    match_label: str, match_color: str):
    """Renders a single job recommendation card."""

    color_map = {
        "green":  "#c9a84c",
        "orange": "#b07030",
        "red":    "#a04848",
    }
    color = color_map.get(match_color, "#8a8070")

    st.markdown(f"""
    <div class="job-card">
        <div style="display: flex; justify-content: space-between; align-items: center; gap:16px;">
            <div style="min-width:0;">
                <div style="display:inline-block; font-family:'JetBrains Mono',monospace; font-size:10.5px; color:#c9a84c; background:rgba(201,168,76,0.10); border:1px solid rgba(201,168,76,0.24); padding:2px 10px; border-radius:6px; margin-bottom:10px; letter-spacing:1px;">RANK #{rank}</div>
                <h3 style="margin: 0; color: #f5f0e0; font-family:'Playfair Display',serif; font-size:19px; font-weight:700; letter-spacing:-0.3px;">{job.get('title', '')}</h3>
                <p style="margin: 7px 0 0 0; color: #5a5040; font-size:13.5px; font-family:'DM Sans',sans-serif;">
                    <span style="color:#a89880; font-weight:600;">{job.get('company', '')}</span>&nbsp;<span style="opacity:.4;">•</span>&nbsp;{job.get('location', '')}&nbsp;<span style="opacity:.4;">•</span>&nbsp;
                    <span style="color:#e2c97e; font-family:'JetBrains Mono',monospace; font-size:11px; letter-spacing:0.5px;">{job.get('source', '').upper()}</span>
                </p>
            </div>
            <div style="text-align: right; flex-shrink:0;">
                <span style="font-size: 36px; font-weight: 800; font-family:'Playfair Display',serif; color: {color}; text-shadow: 0 0 28px {color}55;">{match_percentage}%</span><br>
                <span style="color: {color}; font-size: 11.5px; font-weight:700; letter-spacing:1px; text-transform:uppercase; font-family:'DM Sans',sans-serif;">{match_label}</span>
            </div>
        </div>
        <hr style="margin:16px 0; border:none; height:1px; background:linear-gradient(90deg,transparent,rgba(201,168,76,0.18),transparent);">
        <p style="color: #5a5040; margin: 4px 0; font-size:13.5px; font-family:'DM Sans',sans-serif;">
            <span style="color:#8a8070;">{job.get('experience_required', 'Experience not specified')}</span>&nbsp;<span style="opacity:.4;">•</span>&nbsp;<span style="color:#8a8070;">{job.get('salary', 'Salary not specified')}</span>
        </p>
    </div>
    """, unsafe_allow_html=True)