# tests/test_apply.py

import io
import pytest
from fastapi.testclient import TestClient
from main import app
from app.models.schemas import (
    ApplicationData,
    ResumeData,
    JobData,
    Experience,
    Project,
    Education,
)
from app.agents.cover_letter import build_application_data
from app.parsers.form_filler import detect_portal

client = TestClient(app)


# ─── Sample data ──────────────────────────────────────────────────────────────

sample_resume = ResumeData(
    name="John Doe",
    email="johndoe@gmail.com",
    phone="+91 9876543210",
    skills=["Python", "FastAPI", "SQL", "React", "Git", "Docker"],
    experience=[
        Experience(
            company="ABC Tech",
            role="Software Engineer",
            duration="2 years",
            description="Built REST APIs using FastAPI"
        )
    ],
    projects=[
        Project(
            name="E-Commerce App",
            description="Full stack platform",
            tech_stack=["React", "Node.js", "MongoDB"]
        )
    ],
    education=[
        Education(
            degree="B.Tech",
            field="Computer Science",
            college="ABC University",
            year="2021"
        )
    ],
    certifications=["AWS Certified"],
    total_experience_years=2.0
)

sample_job = JobData(
    title="Python Developer",
    company="Google",
    required_skills=["Python", "FastAPI", "PostgreSQL"],
    preferred_skills=["Docker", "Kubernetes"],
    experience_required="2-4 years",
    education_required="B.Tech Computer Science",
    description="Looking for a Python Developer"
)


# ─── Tests for detect_portal ──────────────────────────────────────────────────

def test_detect_portal_linkedin():
    url = "https://www.linkedin.com/jobs/view/python-developer-123"
    assert detect_portal(url) == "linkedin"


def test_detect_portal_naukri():
    url = "https://www.naukri.com/job-listings-python-developer"
    assert detect_portal(url) == "naukri"


def test_detect_portal_indeed():
    url = "https://in.indeed.com/viewjob?jk=abc123"
    assert detect_portal(url) == "indeed"


def test_detect_portal_glassdoor():
    url = "https://www.glassdoor.co.in/job-listing/python-developer"
    assert detect_portal(url) == "glassdoor"


def test_detect_portal_generic():
    url = "https://careers.google.com/jobs/python-developer"
    assert detect_portal(url) == "generic"


def test_detect_portal_case_insensitive():
    url = "https://www.LinkedIn.com/jobs/view/123"
    assert detect_portal(url) == "linkedin"


# ─── Tests for ApplicationData model ─────────────────────────────────────────

def test_application_data_defaults():
    data = ApplicationData()
    assert data.full_name == ""
    assert data.email == ""
    assert data.phone == ""
    assert data.total_experience_years == 0.0
    assert data.cover_letter == ""
    assert data.linkedin_url == ""
    assert data.github_url == ""
    assert data.portfolio_url == ""


def test_application_data_with_values():
    data = ApplicationData(
        full_name="John Doe",
        email="john@gmail.com",
        phone="+91 9876543210",
        total_experience_years=2.0,
        cover_letter="Dear Hiring Manager...",
        skills_summary="Python, FastAPI, SQL",
    )
    assert data.full_name == "John Doe"
    assert data.email == "john@gmail.com"
    assert data.total_experience_years == 2.0


# ─── Tests for build_application_data ────────────────────────────────────────

def test_build_application_data_returns_dict():
    result = build_application_data(sample_resume, sample_job)
    assert isinstance(result, dict)


def test_build_application_data_has_required_keys():
    result = build_application_data(sample_resume, sample_job)
    assert "full_name" in result
    assert "email" in result
    assert "phone" in result
    assert "cover_letter" in result
    assert "skills_summary" in result
    assert "education_summary" in result


def test_build_application_data_correct_values():
    result = build_application_data(sample_resume, sample_job)
    assert result["full_name"] == "John Doe"
    assert result["email"] == "johndoe@gmail.com"
    assert result["phone"] == "+91 9876543210"


def test_build_application_data_has_cover_letter():
    result = build_application_data(sample_resume, sample_job)
    assert result["cover_letter"] != ""
    assert len(result["cover_letter"]) > 100


def test_build_application_data_skills_summary():
    result = build_application_data(sample_resume, sample_job)
    assert "Python" in result["skills_summary"]


def test_build_application_data_education_summary():
    result = build_application_data(sample_resume, sample_job)
    assert "B.Tech" in result["education_summary"]
    assert "Computer Science" in result["education_summary"]


# ─── Tests for API endpoints ──────────────────────────────────────────────────

def test_apply_endpoint_exists():
    response = client.post("/api/v1/apply")
    assert response.status_code == 422


def test_apply_no_file():
    response = client.post(
        "/api/v1/apply",
        data={"job_url": "https://naukri.com/job-123"}
    )
    assert response.status_code == 422


def test_apply_wrong_file_type():
    fake_image = io.BytesIO(b"fake image content")
    response = client.post(
        "/api/v1/apply",
        files={"file": ("resume.jpg", fake_image, "image/jpeg")},
        data={"job_url": "https://naukri.com/job-123"}
    )
    assert response.status_code == 400


def test_apply_no_job_url():
    fake_pdf = io.BytesIO(b"fake pdf content")
    response = client.post(
        "/api/v1/apply",
        files={"file": ("resume.pdf", fake_pdf, "application/pdf")},
    )
    assert response.status_code == 422


def test_apply_from_recommendation_endpoint_exists():
    response = client.post("/api/v1/apply/from-recommendation")
    assert response.status_code == 422


def test_apply_from_recommendation_wrong_file_type():
    fake_image = io.BytesIO(b"fake image content")
    response = client.post(
        "/api/v1/apply/from-recommendation",
        files={"file": ("resume.jpg", fake_image, "image/jpeg")},
        data={
            "job_url": "https://naukri.com/job-123",
            "job_title": "Python Developer",
            "job_company": "Google",
        }
    )
    assert response.status_code == 400