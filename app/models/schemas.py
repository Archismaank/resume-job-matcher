# app/models/schemas.py

from pydantic import BaseModel, field_validator
from typing import Optional


# ─── Resume Models ────────────────────────────────────────────────────────────

class Experience(BaseModel):
    # One job entry in work experience
    company: str = ""
    role: str = ""
    duration: str = ""        # e.g. "2 years", "6 months"
    description: str = ""     # what they did in that role


class Project(BaseModel):
    # One project entry
    name: str = ""
    description: str = ""
    tech_stack: list[str] = []   # e.g. ["Python", "React", "MongoDB"]


class Education(BaseModel):
    # One education entry
    degree: str = ""             # e.g. "B.Tech", "MBA"
    field: str = ""              # e.g. "Computer Science"
    college: str = ""
    year: Optional[str] = None   # graduation year

    @field_validator("year", mode="before")
    @classmethod
    def convert_year_to_string(cls, v):
        if v is None:
            return None
        return str(v)

class ResumeData(BaseModel):
    # The complete structured resume
    name: str = ""
    email: str = ""
    phone: str = ""
    skills: list[str] = []
    experience: list[Experience] = []
    projects: list[Project] = []
    education: list[Education] = []
    certifications: list[str] = []
    total_experience_years: float = 0.0


# ─── Job Models ───────────────────────────────────────────────────────────────

class JobData(BaseModel):
    # The structured job posting data
    title: str = ""
    company: str = ""
    required_skills: list[str] = []
    preferred_skills: list[str] = []
    experience_required: str = ""    # e.g. "2-4 years"
    education_required: str = ""
    description: str = ""


# ─── Analysis Models ──────────────────────────────────────────────────────────

class SkillGap(BaseModel):
    # One missing skill with details
    skill: str
    importance: str     # "must-have", "nice-to-have", "bonus"
    reason: str         # why this skill matters for the job


class AnalysisResult(BaseModel):
    # The final output we show the user
    match_percentage: float
    matched_skills: list[str] = []
    missing_skills: list[SkillGap] = []
    bonus_skills: list[str] = []      # skills you have that aren't required but impressive
    experience_fit: str = ""          # "under", "match", "over"
    summary: str = ""                 # 2-3 line human readable summary
    resume_tips: list[str] = []       # suggestions to improve resume for this job

# API Request Model -------------------------------------------

class AnalyzeWithURLRequest(BaseModel):
    # reuqest model for analyzing resume against a job url
    job_url : str

class AnalyzeWithTextRequest(BaseModel):
    # request model for analyzing resume against posted job text (the fallback function)
    job_text : str

# API Response Model ---------------------------------------

class AnalyzeResponse(BaseModel):
    # this is the complete response returned to the frontend 
    success : bool
    analysis_id : str # unique ID for this analysis
    resume : ResumeData
    job  : JobData
    analysis : AnalysisResult
    match_label : str
    match_color : str
    error : Optional[str] = None

class ErrorResponse(BaseModel):
    # Returned when something goes wrong
    success : bool = False
    error : str
    detail : Optional[str] = None


# Recommendation Models ----------------------------------------

class JobListing(BaseModel):
    title : str = ""
    company : str = ""
    location : str = ""
    url : str = ""
    description : str = ""
    required_skills : list[str] = []
    preferred_skills : list[str] = []
    experience_required : str = ""
    education_required : str = ""
    salary : str = ""
    source : str = ""
    posted_date : str = ""

class JobRecommendation(BaseModel):
    # A job listing its match analysis
    rank : int
    match_percentage : float
    match_label : str
    match_color : str
    job : JobListing
    matched_skills : list[str] = []
    missing_skills : list[SkillGap] = []
    bonus_skills : list[str] = []
    summary : str = ""

class SearchPreferences(BaseModel):
    location : str = ""
    employment_type : str = "FULLTIME"
    remote_only : bool = False

class RecommendResponse(BaseModel):
    # complete response for mode 2 ->  getting job recommendation
    success : bool
    resume : ResumeData
    total_jobs_found : int  # total jobs found accross each portal
    total_jobs_analyzed : int  # how many jobs we have analyzed
    recommendation : list[JobRecommendation] = []
    search_query : str = ""  # what we searched for
    preferences : Optional[SearchPreferences] = None
    error : Optional[str] = None


# Apply model ---------------------------------------------------------

class ApplicationData(BaseModel):
    full_name : str = ""
    email : str = ""
    phone : str = ""
    total_experience_years : float = 0.0
    skills_summary : str = ""
    education_summary : str = ""
    cover_letter : str = ""
    linkedin_url : str = ""
    github_url : str = ""
    portfolio_url : str = ""

class ApplyRequest(BaseModel):
    job_url : str
    resume_data : ResumeData
    job_data : JobData

class ApplyResponse(BaseModel):
    # Response after attempting to pre-fill
    success: bool
    job_url: str
    application_data: ApplicationData  # what we pre-filled
    fields_filled: list[str] = []      # which fields we successfully filled
    fields_failed: list[str] = []      # which fields we couldn't fill
    message: str = ""                  # human readable status message
    error: Optional[str] = None


# ─── Auth Schemas ─────────────────────────────────────────────────────────────

class SignupRequest(BaseModel):
    # Data required to create a new account
    name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    # Data required to log in
    email: str
    password: str


class TokenResponse(BaseModel):
    # Returned after successful signup or login
    access_token: str
    token_type: str = "bearer"
    user_id: int
    name: str
    email: str


class UserResponse(BaseModel):
    # Public user profile — no password exposed
    id: int
    name: str
    email: str
    phone: str = ""
    linkedin_url: str = ""
    github_url: str = ""
    portfolio_url: str = ""

    class Config:
        from_attributes = True   # allows building from SQLAlchemy ORM objects
