import pytest
from pathlib import Path
from app.parsers.resume import extract_text, extract_text_from_docx, extract_text_from_pdf
from app.agents.analyzer import extract_resume_data
from app.models.schemas import ResumeData

SAMPLE_DATA_DIR = Path("tests/sample_data") # path of our sample data folder

# Test for extract_text function ----------------------------------

def test_extract_text_unsupported_format():
    # this will raise error for unspported file type
    with pytest.raises(ValueError) as error:
        extract_text("resume.jpg")
    assert "Unsupported file type" in str(error.value)

def test_extract_text_file_not_found():
    # this will raise error if file doesn't exist.
    with pytest.raises(FileNotFoundError):
        extract_text("nonexistent_file.pdf")

def test_extract_text_wrong_extension_for_pdf():
    # this will raise an error if file is not a pdf 
    with pytest.raises((ValueError, FileNotFoundError)):
        extract_text_from_pdf("resume.docx")

def test_extract_text_wrong_extension_for_docx():
    # this will raise an error if file is not a docx
    with pytest.raises((ValueError, FileNotFoundError)):
        extract_text_from_docx("resume.pdf")


# Test for sample text file ----------------------------------------

def test_sample_resume_text_exists():
    sample_path = SAMPLE_DATA_DIR / "sample_resume.txt"
    assert sample_path.exists()

def test_sample_resume_text_has_content():
    sample_path = SAMPLE_DATA_DIR / "sample_resume.txt"
    content = sample_path.read_text()
    assert len(content) > 100

def test_sample_resume_contains_key_sections():
    # this check our sample resume file text
    sample_path = SAMPLE_DATA_DIR / "sample_resume.txt"
    content = sample_path.read_text().lower()
    assert "skills" in content
    assert "experience" in content
    assert "education" in content
    assert "projects" in content

# Test for AI extraction ---------------------------------------------

def test_extract_resume_data_returns_correct_type():
    sample_path = SAMPLE_DATA_DIR / "sample_resume.txt"
    raw_text = sample_path.read_text()

    # calling OpenAI to extract structured data
    result = extract_resume_data(raw_text)

    # checking if it returns a ResumeData object or not
    assert isinstance(result, ResumeData)

def test_extract_resume_data_gets_name():
    sample_path = SAMPLE_DATA_DIR / "sample_resume.txt"
    raw_text = sample_path.read_text()
    result = extract_resume_data(raw_text)

    # checking if name was extracted correctly
    assert result.name != ""
    assert "john" in result.name.lower()

def test_extract_resume_data_gets_email():
    sample_path = SAMPLE_DATA_DIR / "sample_resume.txt"
    raw_text = sample_path.read_text()
    result = extract_resume_data(raw_text)

    assert result.email != ""
    assert "@" in result.email

def test_extract_resume_data_gets_skills():
    sample_path = SAMPLE_DATA_DIR / "sample_resume.txt"
    raw_text = sample_path.read_text()
    result = extract_resume_data(raw_text)

    # cheking if skills were extracted as a list
    assert isinstance(result.skills, list)
    assert len(result.skills) > 0

    # check some known skills from our sample
    skills_lower = [s.lower() for s in result.skills]
    assert "python" in skills_lower

def test_extract_resume_data_gets_project():
    sample_path = SAMPLE_DATA_DIR / "sample_resume.txt"
    raw_text = sample_path.read_text()
    result = extract_resume_data(raw_text)

    # check projects were extracted
    assert isinstance(result.projects, list)
    assert len(result.projects) > 0

    # check first project has a name and tech_stack
    first_project = result.projects[0]
    assert first_project.name != ""
    assert isinstance(first_project.tech_stack, list)

def test_extract_resume_data_gets_education():
    sample_path = SAMPLE_DATA_DIR / "sample_resume.txt"
    raw_text = sample_path.read_text()
    result = extract_resume_data(raw_text)

    # check education was extracted 
    assert isinstance(result.education, list)
    assert len(result.education) > 0