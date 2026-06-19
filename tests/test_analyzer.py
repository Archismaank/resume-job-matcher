import pytest
from pathlib import Path
from app.agents.analyzer import analyze_resume_against_job
from app.agents.scorer import calculate_match_percentage, get_match_label, get_match_color
from app.models.schemas import ResumeData, JobData, AnalysisResult, Experience, Project, Education

# Test for Scorer ---------------------------------------------

def test_calculate_macth_percentage_perfect_score():
    result = calculate_match_percentage(
        required_skills_score = 100,
        preferred_skills_score = 100,
        experience_score = 100,
        education_score = 100,
        projects_score = 100,
    )
    assert result == 100.0

def test_calculate_match_percentage_zero_score():
    result = calculate_match_percentage(
        required_skills_score = 0,
        preferred_skills_score = 0,
        experience_score = 0,
        education_score = 0,
        projects_score = 0,
    )
    assert result == 0.0

def test_calculate_match_percentage_weighted():
    result = calculate_match_percentage(
        required_skills_score = 100,
        preferred_skills_score = 0,
        experience_score = 0,
        education_score = 0,
        projects_score = 0,
    )
    assert result == 40.0

def test_calculate_match_percentage_returns_float():
    result = calculate_match_percentage(
        required_skills_score = 75,
        preferred_skills_score = 50,
        experience_score = 100,
        education_score = 100,
        projects_score = 80,
    )
    assert isinstance(result, float)

def test_calculate_match_percentage_rounded():
    result = calculate_match_percentage(
        required_skills_score = 33,
        preferred_skills_score = 33,
        experience_score = 33,
        education_score = 33,
        projects_score = 33,
    )
    assert result == round(result, 1)


# Test for match labels ------------------------------------------

def test_get_match_label_excellent():
    assert get_match_label(90) == "Excellent Match"
    assert get_match_label(85) == "Excellent Match"

def test_get_match_label_good():
    assert get_match_label(75) == "Good Match"
    assert get_match_label(70) == "Good Match"

def test_get_match_label_moderate():
    assert get_match_label(60) == "Moderate Match"
    assert get_match_label(55) == "Moderate Match"

def test_get_match_label_weak():
    assert get_match_label(45) == "Weak Match"
    assert get_match_label(40) == "Weak Match"

def test_get_match_label_poor():
    assert get_match_label(30) == "Poor Match"
    assert get_match_label(0) == "Poor Match"


# Test for match color ---------------------------------------------

def test_get_match_color_green():
    assert get_match_color(80) == "green"
    assert get_match_color(70) == "green"


def test_get_match_color_orange():
    assert get_match_color(60) == "orange"
    assert get_match_color(50) == "orange"


def test_get_match_color_red():
    assert get_match_color(40) == "red"
    assert get_match_color(0) == "red"

    
# Test for full analysis -------------------------------------------

# building sample resume and job objects for testing.

sample_resume = ResumeData(
    name = "John Doe",
    email = "johndoe@gmail.com",
    phone = "+91 9876543210",
    skills = ["Python", "FastAPI", "SQL", "React", "Git", "Docker"],
    experience = [
        Experience(
            company = "ABC Tech",
            role = "Software Engineer",
            duration = "2 years",
            description = "Built Rest APIs using FastAPI and Python"
        )
    ],
    projects = [
        Project(
            name = "E-Commerce App",
            description = "Full stack e-commerce platform",
            tech_stack = ["React", "Node.js", "MongoDB"]
        )
    ],
    education = [
        Education(
            degree = "B.Tech",
            field = "computer Science",
            college = "ABC University",
            year = "2021"
        )
    ],
    certifications = ["AWS Certified Developer"],
    total_experience_years = 2.0
)

sample_job = JobData(
    title = "Python Developer",
    company = "Google",
    required_skills = ["Python", "FastAPI", "PostgreSQL", "REST APIs", "Git"],
    preferred_skills = ["Docker", "Kubernetes", "Redis"],
    experience_required = "2-4 years",
    education_required = "B.Tech Computer Science",
    description = "Looking for a python Developer to build scalable backend services"
)

def test_analyze_returns_correct_type():
    result = analyze_resume_against_job(sample_resume, sample_job)
    assert isinstance(result, AnalysisResult)

def test_analyze_returns_match_percentage():
    result = analyze_resume_against_job(sample_resume, sample_job)
    assert isinstance(result.match_percentage, float)
    assert 0 <= result.match_percentage <= 100

def test_analyze_returns_matched_skills():
    result = analyze_resume_against_job(sample_resume, sample_job)
    assert isinstance(result.matched_skills, list)
    assert len(result.matched_skills) > 0

def test_analyze_returns_missing_skills():
    result = analyze_resume_against_job(sample_resume, sample_job)
    assert isinstance(result.missing_skills, list)

def test_analyze_returns_experience_fit():
    result = analyze_resume_against_job(sample_resume, sample_job)
    assert result.experience_fit in ["under", "match", "over"]

def test_analyze_returns_summary():
    result = analyze_resume_against_job(sample_resume, sample_job)
    assert result.summary != ""
    assert len(result.summary) > 50

def test_analyze_returns_resume_tips():
    result = analyze_resume_against_job(sample_resume, sample_job)
    assert isinstance(result.resume_tips, list)
    assert len(result.resume_tips) > 0

def test_analyze_match_percentage_reasonable():
    result = analyze_resume_against_job(sample_resume, sample_job)
    assert result.match_percentage > 50