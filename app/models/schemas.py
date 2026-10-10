# app/models/schemas.py

from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime


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
    semantic_similarity: float = 0.0   # cosine similarity score (0-100) from RAG embeddings
    matched_skills: list[str] = []
    missing_skills: list[SkillGap] = []
    bonus_skills: list[str] = []      # skills you have that aren't required but impressive
    experience_fit: str = ""          # "under", "match", "over"
    summary: str = ""                 # 2-3 line human readable summary
    resume_tips: list[str] = []       # suggestions to improve resume for this job

# API Request Model -------------------------------------------

class AnalyzeWithURLRequest(BaseModel):
    # request model for analyzing resume against a job url
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
    # A job listing with its match analysis
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
    # complete response for mode 2 -> getting job recommendation
    success : bool
    resume : ResumeData
    total_jobs_found : int  # total jobs found across each portal
    total_jobs_analyzed : int  # how many jobs we have analyzed
    recommendation : list[JobRecommendation] = []
    search_query : str = ""  # what we searched for
    preferences : Optional[SearchPreferences] = None
    error : Optional[str] = None


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
    is_verified: bool = False

    class Config:
        from_attributes = True   # allows building from SQLAlchemy ORM objects

class UpdateProfileRequest(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


# ─── History Schemas ──────────────────────────────────────────────────────────

class AnalysisHistoryResponse(BaseModel):
    id: int
    job_title: str
    company: str
    job_url: Optional[str] = None
    match_percentage: float
    full_result_json: str
    created_at: str = ""

    @field_validator("created_at", mode="before")
    @classmethod
    def coerce_datetime_to_str(cls, v):
        """Pydantic V2 does not auto-coerce datetime → str. We do it explicitly."""
        if isinstance(v, datetime):
            return v.isoformat()
        return str(v) if v is not None else ""

    class Config:
        from_attributes = True


class RecommendationHistoryResponse(BaseModel):
    id: int
    search_query: str
    total_jobs_found: int
    full_result_json: str
    created_at: str = ""

    @field_validator("created_at", mode="before")
    @classmethod
    def coerce_datetime_to_str(cls, v):
        """Pydantic V2 does not auto-coerce datetime → str. We do it explicitly."""
        if isinstance(v, datetime):
            return v.isoformat()
        return str(v) if v is not None else ""

    class Config:
        from_attributes = True
