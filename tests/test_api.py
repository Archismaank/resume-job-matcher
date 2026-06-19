# tests/test_api.py
import io
from fastapi.testclient import TestClient
from main import app

# This creates a fake client that can call our API without a real server
client = TestClient(app)


def test_root_returns_200():
    # Call the / route and check we get a 200 (success) status code
    response = client.get("/")
    assert response.status_code == 200


def test_root_has_message():
    # Check the response actually contains a message key
    response = client.get("/")
    data = response.json()
    assert "message" in data


def test_health_check_returns_ok():
    # Call /health and check status is "ok"
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_health_check_has_correct_fields():
    # Check all expected fields are present
    response = client.get("/health")
    data = response.json()
    assert "environment" in data
    assert "ai_provider" in data
    assert data["ai_provider"] == "openai"

def test_router_health_check():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["router"] == "analyze"

# Test for file validation ------------------------------------

def test_analyze_url_no_file():
    response = client.post(
        "/api/v1/analyze/url", 
        data = {"job_url" : "https://example.com/job"}
    )
    assert response.status_code == 422

def test_analyze_url_wrong_file_type():
    # should fail when file is  not PDF or DOCX.
    fake_image = io.BytesIO(b"fake image content")
    response = client.post(
        "/api/v1/analyze/url",
        files = {"file" : ("resume.jpg", fake_image, "image/jpeg")},
        data = {"job_url" : "https://example.com/job"}
    )
    assert response.status_code == 400

def test_analyze_url_no_job_url():
    # it will fail when no job url is provided.
    fake_pdf = io.BytesIO(b"fake pdf content")
    response = client.post(
        "/api/v1/analyze/url",
        files = {"file" : ("resume.pdf", fake_pdf, "application/pdf")},
    )
    assert response.status_code == 422


def test_analyze_text_no_file():
    # Should fail when no file is provided
    response = client.post(
        "/api/v1/analyze/text",
        data={"job_text": "We are looking for a Python Developer"}
    )
    assert response.status_code == 422


def test_analyze_text_wrong_file_type():
    # Should fail when file is not PDF or DOCX
    fake_image = io.BytesIO(b"fake image content")
    response = client.post(
        "/api/v1/analyze/text",
        files={"file": ("resume.jpg", fake_image, "image/jpeg")},
        data={"job_text": "We are looking for a Python Developer"}
    )
    assert response.status_code == 400

def test_analyze_text_no_job_text():
    # Should fail when no job text is provided
    fake_pdf = io.BytesIO(b"fake pdf content")
    response = client.post(
        "/api/v1/analyze/text",
        files={"file": ("resume.pdf", fake_pdf, "application/pdf")},
    )
    assert response.status_code == 422