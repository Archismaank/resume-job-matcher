# tests/test_recommender.py

import pytest
from app.models.schemas import (
    ResumeData,
    JobListing,
    SearchPreferences,
    Experience,
    Project,
    Education,
)
from app.agents.recommender import (
    deduplicate_jobs,
    convert_listing_to_job_data,
)


# ─── Sample data for testing ──────────────────────────────────────────────────

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
            description="Built REST APIs using FastAPI and Python"
        )
    ],
    projects=[
        Project(
            name="E-Commerce App",
            description="Full stack e-commerce platform",
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
    certifications=["AWS Certified Developer"],
    total_experience_years=2.0
)

sample_preferences = SearchPreferences(
    location="Bangalore",
    employment_type="FULLTIME",
    remote_only=False,
)


# ─── Tests for deduplicate_jobs ───────────────────────────────────────────────

def test_deduplicate_removes_exact_duplicates():
    jobs = [
        JobListing(title="Python Developer", company="Google", source="adzuna"),
        JobListing(title="Python Developer", company="Google", source="jsearch"),
    ]
    result = deduplicate_jobs(jobs)
    assert len(result) == 1


def test_deduplicate_keeps_different_jobs():
    jobs = [
        JobListing(title="Python Developer", company="Google", source="adzuna"),
        JobListing(title="React Developer", company="Google", source="jsearch"),
    ]
    result = deduplicate_jobs(jobs)
    assert len(result) == 2


def test_deduplicate_case_insensitive():
    jobs = [
        JobListing(title="Python Developer", company="Google", source="adzuna"),
        JobListing(title="python developer", company="google", source="jsearch"),
    ]
    result = deduplicate_jobs(jobs)
    assert len(result) == 1


def test_deduplicate_empty_list():
    result = deduplicate_jobs([])
    assert result == []


def test_deduplicate_single_job():
    jobs = [
        JobListing(title="Python Developer", company="Google", source="adzuna"),
    ]
    result = deduplicate_jobs(jobs)
    assert len(result) == 1


def test_deduplicate_keeps_first_occurrence():
    jobs = [
        JobListing(
            title="Python Developer",
            company="Google",
            source="adzuna",
            url="https://adzuna.com/job1"
        ),
        JobListing(
            title="Python Developer",
            company="Google",
            source="jsearch",
            url="https://jsearch.com/job1"
        ),
    ]
    result = deduplicate_jobs(jobs)
    # Should keep the first one (from adzuna)
    assert result[0].source == "adzuna"


# ─── Tests for convert_listing_to_job_data ────────────────────────────────────

def test_convert_listing_to_job_data_basic():
    listing = JobListing(
        title="Python Developer",
        company="Google",
        required_skills=["Python", "FastAPI"],
        preferred_skills=["Docker"],
        experience_required="2-4 years",
        description="Looking for a Python Developer",
        source="adzuna"
    )
    job_data = convert_listing_to_job_data(listing)
    assert job_data.title == "Python Developer"
    assert job_data.company == "Google"
    assert job_data.required_skills == ["Python", "FastAPI"]
    assert job_data.preferred_skills == ["Docker"]
    assert job_data.experience_required == "2-4 years"


def test_convert_listing_preserves_skills():
    listing = JobListing(
        title="React Developer",
        company="Flipkart",
        required_skills=["React", "JavaScript", "CSS"],
        preferred_skills=["TypeScript", "Redux"],
        source="jsearch"
    )
    job_data = convert_listing_to_job_data(listing)
    assert len(job_data.required_skills) == 3
    assert len(job_data.preferred_skills) == 2
    assert "React" in job_data.required_skills


def test_convert_listing_handles_empty_skills():
    listing = JobListing(
        title="Python Developer",
        company="Google",
        source="naukri"
    )
    job_data = convert_listing_to_job_data(listing)
    assert job_data.required_skills == []
    assert job_data.preferred_skills == []


# ─── Tests for SearchPreferences model ───────────────────────────────────────

def test_search_preferences_defaults():
    prefs = SearchPreferences()
    assert prefs.location == ""
    assert prefs.employment_type == "FULLTIME"
    assert prefs.remote_only == False


def test_search_preferences_custom():
    prefs = SearchPreferences(
        location="Mumbai",
        employment_type="PARTTIME",
        remote_only=True,
    )
    assert prefs.location == "Mumbai"
    assert prefs.employment_type == "PARTTIME"
    assert prefs.remote_only == True


# ─── Tests for API endpoint ───────────────────────────────────────────────────

import io
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_recommend_endpoint_exists():
    # Check endpoint exists
    response = client.post("/api/v1/recommend")
    # 422 means endpoint exists but required fields missing
    assert response.status_code == 422


def test_recommend_no_file():
    response = client.post(
        "/api/v1/recommend",
        data={"location": "Bangalore"}
    )
    assert response.status_code == 422


def test_recommend_wrong_file_type():
    fake_image = io.BytesIO(b"fake image content")
    response = client.post(
        "/api/v1/recommend",
        files={"file": ("resume.jpg", fake_image, "image/jpeg")},
        data={"location": "Bangalore"}
    )
    assert response.status_code == 400