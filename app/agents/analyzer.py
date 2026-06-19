import json
from openai import OpenAI
from app.config import settings
from app.models.schemas import ResumeData, JobData, AnalysisResult, SkillGap
from app.agents.prompts import RESUME_EXTRACTION_PROMPT, JOB_EXTRACTION_PROMPT, ANALYSIS_PROMPT
from app.agents.scorer import calculate_match_percentage

# now here I'm creating one OpenAI client that we resume everywhere
client = OpenAI(api_key = settings.openai_api_key)

def clean_json_response(raw_response: str) -> str:
    """
    Cleans OpenAI response and extracts pure JSON from it.
    Finds the first { and last } and extracts everything between them.
    This is the most reliable approach regardless of markdown formatting.
    """
    cleaned = raw_response.strip()

    # Find the first { and last } in the response
    # Everything between them is our JSON
    start = cleaned.find("{")
    end = cleaned.rfind("}")

    if start == -1 or end == -1:
        raise ValueError(f"No valid JSON found in response: {cleaned}")

    # Extract just the JSON part
    cleaned = cleaned[start:end + 1]

    return cleaned


def extract_resume_data(raw_text: str) -> ResumeData:
    """
    Takes raw resume text and sends it to OpenAI.
    OpenAI extracts the structured data and returns JSON.
    We validate that JSON with Pydantic and return a ResumeData object.
    """

    prompt = RESUME_EXTRACTION_PROMPT.format(resume_text = raw_text)

    # now sending the prompt to OpenAI
    response = client.chat.completions.create(
        model = "gpt-4o-mini",
        messages = [
            {
                "role" : "system",
                "content" : "You are an expert resume parser. Always respond with valid JSON only."
            },
            {
                "role" : "user",
                "content" : prompt
            }
        ], 
        temperature = 0,
        max_tokens = 2000,
        seed = 42,
    )

    # Getting the text response from OpenAI
    raw_response = response.choices[0].message.content.strip()

    # Sometimes OpenAI wraps JSON in markdown code blocks like ```json ... ``` , so we will clean that up.
    clean_response = clean_json_response(raw_response)
    
    data = json.loads(clean_response) # json string -> python dict

    # validating the dict with our Pydantic model so that it ensures all fields are the right type
    resume_data = ResumeData(**data)

    return resume_data

def extract_job_data(raw_text : str) -> JobData:
    """
    Takes raw job posting text and sends it to OpenAI.
    OpenaAI extracts the structured data and return JSON.
    We validate that JSON with Pydantic and return a JobData object.
    """

    prompt = JOB_EXTRACTION_PROMPT.format(job_text = raw_text)

    response = client.chat.completions.create(
        model = "gpt-4o-mini",
        messages = [
            {
                "role" : "system",
                "content" : "You are an expert job posting parser. Always respond with valid JSON only."
            },
            {
                "role" : "user",
                "content" : prompt
            }
        ],
        temperature = 0,
        max_tokens = 4000,
        seed = 42,
    )

    raw_response = response.choices[0].message.content.strip()

    clean_response = clean_json_response(raw_response)

    data = json.loads(clean_response)

    if not isinstance(data, dict):
        raise ValueError(
            f"Job extraction failed: AI returned '{type(data).__name__}' instead of a JSON object. "
            "The page content may not contain a valid job description."
        )

    job_data = JobData(**data)

    return job_data


def analyze_resume_against_job(
        resume : ResumeData,
        job : JobData
) -> AnalysisResult:
    """
    Takes a ResumeData and JobData object.
    Sends both to OpenAI for intelligent comparison.
    Calculates match percentage using weighted formula.
    Returns a complete AnalysisResult object.
    """

    prompt = ANALYSIS_PROMPT.format(
        # Resume fields
        name = resume.name,
        skills = ", ".join(resume.skills),
        experience = ", ".join(
            [f"{e.role} at {e.company} ({e.duration})" for e in resume.experience]
        ),
        projects = ", ".join(
            [f"{p.name} ({", ".join(p.tech_stack)})" for p in resume.projects]
        ),
        education = ", ".join(
            [f"{e.degree} in {e.field} from {e.college}" for e in resume.education]
        ),
        total_experience_years = resume.total_experience_years,
        certifications = ", ".join(resume.certifications),

        # Job fields
        job_title = job.title,
        job_company = job.company,
        required_skills = ", ".join(job.required_skills),
        preferred_skills = ", ".join(job.preferred_skills),
        experience_required = job.experience_required,
        education_required = job.education_required,
        job_description = job.description,
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role" : "system",
                "content" : "You are an expert technical recruiter. Always respond with valid JSON only."
            },
            {
                "role" : "user",
                "content" : prompt
            }
        ],
        temperature=0,
        max_tokens = 3000,
        seed = 42,
    )

    raw_response = response.choices[0].message.content
    clean_response = clean_json_response(raw_response)

    data = json.loads(clean_response)

    if not isinstance(data, dict):
        raise ValueError(
            f"Resume analysis failed: AI returned '{type(data).__name__}' instead of a JSON object. "
            "This usually means the job description was too short or unreadable."
        )

    # calculating match percentage using the weighted formula we defined.
    match_percentage = calculate_match_percentage(
        required_skills_score = data.get("required_skills_score", 0),
        preferred_skills_score = data.get("preferred_skills_score", 0),
        experience_score = data.get("experience_score", 0),
        education_score = data.get("education_score", 0),
        projects_score = data.get("projects_score", 0),
    )

    # building skillgap objects from missing skills.
    # Guard: skip any None or non-dict entries the AI may return
    missing_skills = [
        SkillGap(
            skill      = s.get("skill", ""),
            importance = s.get("importance", "nice-to-have"),
            reason     = s.get("reason", "")
        )
        for s in data.get("missing_skills", [])
        if s and isinstance(s, dict)   # skip None / string items
    ]

    # Build and return the final AnalysisResult
    result = AnalysisResult(
        match_percentage = match_percentage,
        matched_skills = data.get("matched_skills", []),
        missing_skills = missing_skills,
        bonus_skills = data.get("bonus_skills", []),
        experience_fit = data.get("experience_fit", []),
        summary = data.get("summary", ""),
        resume_tips = data.get("resume_tips", []),
    )

    return result



