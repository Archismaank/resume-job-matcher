from openai import OpenAI
from app.config import settings
from app.models.schemas import ResumeData, JobData
from app.agents.prompts import COVER_LETTER_PROMPT

client = OpenAI(api_key = settings.openai_api_key)

def generate_cover_letter(
    resume : ResumeData,
    job : JobData,
) -> str:
    """
    Generates a personalized cover letter for a specific job.
    Takes resume and job data and returns a cover letter string.
    """

    prompt = COVER_LETTER_PROMPT.format(
        name = resume.name,
        skills = ", ".join(resume.skills[:10]),
        experience = ", ".join([
            f"{e.role} at {e.company} ({e.duration})"
            for e in resume.experience
        ]),
        total_experience_years = resume.total_experience_years,
        education = ", ".join([
            f"{e.degree} in {e.field} from {e.college}"
            for e in resume.education
        ]),
        job_title = job.title,
        job_company = job.company,
        required_skills = ", ".join(job.required_skills),
        job_description = job.description[:500],
    )

    response = client.chat.completions.create(
        model = "gpt-4o-mini",
        messages = [
           {
                "role" : "system",
                "content" : "You are an expert cover letter writer. Write professional, concise cover letters."
           },
           {
               "role" : "user",
               "content" : prompt
           }
        ],
        temperature=0.7,
        max_tokens = 500,
    )

    cover_letter = response.choices[0].message.content.strip()
    return cover_letter


def build_application_data(
    resume : ResumeData,
    job : JobData,
) -> dict:
    """
    Builds a dictionary of all aplication data 
    ready to be used for for form filling.
    """

    cover_letter = generate_cover_letter(resume, job)
    skills_summary = ", ".join(resume.skills[:15])
    education_summary = " | ".join([
        f"{e.degree} in {e.field} from {e.college}"
        for e in resume.education
    ])

    return {
        "full_name": resume.name,
        "email": resume.email,
        "phone": resume.phone,
        "total_experience_years": resume.total_experience_years,
        "skills_summary": skills_summary,
        "education_summary": education_summary,
        "cover_letter": cover_letter,
        "linkedin_url": "",
        "github_url": "",
        "portfolio_url": "",
    }
