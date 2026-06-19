import pytest
from pathlib import Path
from app.parsers.job_scraper import scrape_job_posting, scrape_job_posting_fallback
from app.agents.analyzer import extract_job_data
from app.models.schemas import JobData

SAMPLE_DATA_DIR = Path("tests/sample_data")

# Test for url validation ---------------------------------------------------------

def test_scrape_invalid_url():
    # it will raise error for invalid url 
    with pytest.raises(ValueError) as error:
        scrape_job_posting("linkedin.com/job/123")
    assert "Invalid URL" in str(error.value)

def test_scrape_url_without_https():
    # should raise error if url dosen't start with http
    with pytest.raises(ValueError):
        scrape_job_posting("www.google.com/jobs")


# Test for fallback function --------------------------------------------------------

def test_fallback_empty_text():
    # it will raise error for empty text
    with pytest.raises(ValueError) as error:
        scrape_job_posting_fallback("")
    assert "empty" in str(error.value).lower()

def test_fallback_whitespace_only():
    with pytest.raises(ValueError):
        scrape_job_posting_fallback("        ")

def test_fallback_returns_clean_text():
    # should return clean text 
    raw = "  Python Devloper  \n\n  Google  \n\n  "
    result = scrape_job_posting_fallback(raw)
    assert "Python Devloper" in result
    assert "Google" in result

def test_fallback_removes_empty_lines():
    # should return clean text 
    raw = "  Python Devloper  \n\n  Google  \n\n  "
    result = scrape_job_posting_fallback(raw)
    lines = result.splitlines()
    # no line should be empty
    assert all(line.strip() for line in lines)


# Test for sample job file --------------------------------------------------------

def test_sample_job_file_exists():
    sample_path = SAMPLE_DATA_DIR / "sample_job.txt"
    assert sample_path.exists()

def test_sample_job_has_content():
    sample_path = SAMPLE_DATA_DIR / "sample_job.txt"
    content = sample_path.read_text()
    assert len(content) > 100

def test_sample_job_contains_key_sections():
    sample_path = SAMPLE_DATA_DIR / "sample_job.txt"
    content = sample_path.read_text().lower()
    assert "skills" in content
    assert "experience" in content
    assert "python" in content


# Test for AI job extraction -----------------------------------------------------

def test_extract_job_data_returns_correct_type():
    sample_path = SAMPLE_DATA_DIR / "sample_job.txt"
    raw_text = sample_path.read_text()
    result = extract_job_data(raw_text)
    assert isinstance(result, JobData)

def test_extract_job_data_gets_title():
    sample_path = SAMPLE_DATA_DIR / "sample_job.txt"
    raw_text = sample_path.read_text()
    result = extract_job_data(raw_text)
    assert result.title != ""
    assert "python" in result.title.lower()

def test_extract_job_data_gets_required_skills():
    sample_path = SAMPLE_DATA_DIR / "sample_job.txt"
    raw_text = sample_path.read_text()
    result = extract_job_data(raw_text)
    assert isinstance(result.required_skills, list)
    assert len(result.required_skills) > 0
    skills_lower = [s.lower() for s in result.required_skills]
    assert "python" in skills_lower

def test_extract_job_data_gets_preferred_skills():
    sample_path = SAMPLE_DATA_DIR / "sample_job.txt"
    raw_text = sample_path.read_text()
    result = extract_job_data(raw_text)
    assert isinstance(result.preferred_skills, list)

def test_extract_job_data_gets_experience():
    sample_path = SAMPLE_DATA_DIR / "sample_job.txt"
    raw_text = sample_path.read_text()
    result = extract_job_data(raw_text)
    assert result.experience_required != ""