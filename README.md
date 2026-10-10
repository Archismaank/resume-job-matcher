# 🎯 Resume Job Matcher

> An AI-powered career tool that scores how well your resume matches any job posting — and finds the best-fit roles across multiple job portals simultaneously.

---

## ✨ Features

| Feature | Description |
|---|---|
| **Resume Analysis** | Upload your resume (PDF or DOCX) + paste a job URL or description. Get a weighted match score (0–100%), matched/missing/bonus skills, experience fit assessment, and AI-written resume improvement tips. |
| **Job Recommendations** | Searches **Adzuna**, **JSearch (RapidAPI)**, and **Naukri** in parallel. Every result is scored against your resume by AI and ranked by match percentage. |
| **PDF Report** | Download a clean, formatted analysis report with match score, skills breakdown, and resume tips. |
| **Auth System** | JWT-based signup/login. Session survives page refreshes via query params token. |

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | FastAPI + Uvicorn (Python 3.12) |
| **Frontend** | Streamlit |
| **AI** | OpenAI GPT-4o-mini — all extraction + analysis calls |
| **Job Scraping** | Playwright (stealth) + BeautifulSoup |
| **Job APIs** | Adzuna REST API, JSearch via RapidAPI |
| **Database** | SQLite + SQLAlchemy ORM + Alembic migrations |
| **Auth** | JWT (python-jose) + bcrypt password hashing |
| **PDF Generation** | fpdf2 |
| **Package Manager** | [uv](https://docs.astral.sh/uv/) |

---

## 🏗 Architecture Highlights

- **Decoupled client-server** — Streamlit frontend talks to FastAPI backend via REST. No shared state between them.
- **Async parallel job fetching** — `asyncio.gather` fans out to Adzuna + JSearch simultaneously; Naukri runs in a thread executor. All jobs are then analyzed concurrently via `ThreadPoolExecutor`.
- **Deterministic AI** — All OpenAI calls use `temperature=0, seed=42` so identical inputs always produce identical scores.
- **Alembic migrations** — Schema changes auto-apply on server startup. No more `ALTER TABLE` headaches.

### Match Score Formula

```
Match % =  Required Skills   × 40%
         + Work Experience   × 25%
         + Education         × 15%
         + Preferred Skills  × 12%
         + Projects          × 8%
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager

```bash
# Install uv (if you don't have it)
pip install uv
```

### 1. Clone the repo

```bash
git clone https://github.com/Archismaank/resume-job-matcher.git
cd resume-job-matcher
```

### 2. Install dependencies

```bash
uv sync
```

### 3. Install Playwright browser (first time only)

```bash
uv run playwright install chromium
```

### 4. Configure environment variables

```bash
cp .env.example .env
# Open .env and fill in your API keys
```

You'll need:
- **OpenAI API key** — [platform.openai.com](https://platform.openai.com)
- **Adzuna API** (free) — [developer.adzuna.com](https://developer.adzuna.com)
- **JSearch via RapidAPI** (free tier) — [rapidapi.com](https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch)

### 5. Run the app

Open **two terminals**:

**Terminal 1 — Backend (FastAPI)**
```bash
uv run uvicorn main:app --reload
```

**Terminal 2 — Frontend (Streamlit)**
```bash
uv run streamlit run ui/streamlit_app.py
```

| Service | URL |
|---|---|
| Streamlit UI | http://localhost:8501 |
| FastAPI Backend | http://localhost:8000 |
| Swagger API Docs | http://localhost:8000/docs |

---

## 📁 Project Structure

```
resume-job-matcher/
│
├── main.py                   # FastAPI app — routers, CORS, Alembic startup
├── pyproject.toml            # Project metadata + dependencies (uv)
│
├── app/                      # Backend
│   ├── agents/
│   │   ├── analyzer.py       # AI: resume extraction, job extraction, analysis
│   │   ├── recommender.py    # Parallel job search + scoring pipeline
│   │   ├── scorer.py         # Weighted match % formula
│   │   └── prompts.py        # All LLM prompt templates
│   ├── api/
│   │   ├── routes.py         # /analyze/url, /analyze/text, /recommend
│   │   └── auth.py           # /auth/signup, /auth/login, /auth/me
│   ├── db/
│   │   ├── database.py       # SQLAlchemy engine + session
│   │   └── models.py         # User, AnalysisHistory, RecommendationHistory ORM models
│   └── parsers/
│       ├── resume.py         # PDF + DOCX text extraction
│       ├── job_scraper.py    # Playwright scraper for any job URL
│       ├── adzuna_client.py  # Adzuna REST API client
│       └── naukri_scraper.py # Playwright stealth scraper for Naukri
│
├── ui/                       # Frontend
│   ├── streamlit_app.py      # Main app — tabs, auth gate, session management
│   └── components.py        # Reusable UI components (job cards, skill chips, charts)
│
├── migrations/               # Alembic migration files
└── tests/                    # Pytest test suite
```

---

## 🔌 API Reference

All endpoints (except auth) require `Authorization: Bearer <token>` header.

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/analyze/url` | Analyze resume vs a live job URL |
| `POST` | `/api/v1/analyze/text` | Analyze resume vs pasted job description |
| `POST` | `/api/v1/recommend` | Find & rank matching jobs across portals |
| `POST` | `/api/v1/auth/signup` | Register a new user |
| `POST` | `/api/v1/auth/login` | Login and get JWT token |
| `GET` | `/api/v1/auth/me` | Get current user profile |
| `GET` | `/health` | Health check |

Full interactive docs: **http://localhost:8000/docs**

---

## 🧪 Running Tests

```bash
uv run pytest
```

---

## 📄 License

MIT