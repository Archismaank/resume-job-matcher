import asyncio
import uuid
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from app.api.file_handler import save_upload_file, delete_file
from app.api.dependencies import get_current_user
from app.db.models import User
from app.parsers.resume import extract_text
from app.parsers.job_scraper import scrape_job_posting, scrape_job_posting_fallback
from app.agents.analyzer import extract_resume_data, extract_job_data, analyze_resume_against_job
from app.agents.scorer import get_match_label, get_match_color
from app.agents.recommender import generate_recommendations
from app.agents.cover_letter import build_application_data
from app.parsers.form_filler import fill_job_application
from app.models.schemas import (
    AnalyzeResponse, RecommendResponse, SearchPreferences, ApplicationData, ApplyResponse,
)
# APIRouter -> it's like a mini app and we define routes here and register them in main.py
router = APIRouter()

@router.post("/analyze/url", response_model = AnalyzeResponse)
async def analyze_with_url(
    file : UploadFile = File(...),
    job_url : str = Form(...),
    current_user: User = Depends(get_current_user),
):
    """
    Accepts a resume file and job posting url.
    Scrapes the job URL, analyze the resume against it, and returns the full analysis.
    """

    # save the uploaded file
    file_path = await save_upload_file(file)

    try:
        raw_resume_text = extract_text(str(file_path))
        resume_data = extract_resume_data(raw_resume_text)

        # Run sync_playwright in a separate thread — threads have no asyncio
        # event loop, so sync_playwright works without any conflict.
        raw_job_text = await asyncio.to_thread(scrape_job_posting, job_url)

        # Guard: Adzuna/LinkedIn detail URLs often redirect to employer sites
        # or bot-detection pages that return near-empty content.
        if len(raw_job_text.strip()) < 200:
            raise HTTPException(
                status_code=422,
                detail=(
                    "Could not extract job content from this URL. "
                    "The page may have redirected, expired, or blocked the scraper. "
                    "Try pasting the job description directly instead."
                ),
            )

        job_data = extract_job_data(raw_job_text)
        analysis = analyze_resume_against_job(resume_data, job_data)

        return AnalyzeResponse(
            success = True,
            analysis_id = str(uuid.uuid4()),
            resume = resume_data,
            job = job_data,
            analysis = analysis,
            match_label = get_match_label(analysis.match_percentage),
            match_color = get_match_color(analysis.match_percentage),
        )
    except Exception as e:
        # if anything goes wrong return a clear error response
        raise HTTPException(
            status_code = 500,
            detail = str(e)
        )
    finally:
        # we will always delete the uploaded file after processing -> finally always runs even if try or except fails
        delete_file(file_path)


@router.post("/analyze/text", response_model = AnalyzeResponse)
async def analyze_with_text(
    file : UploadFile = File(...),
    job_text : str = Form(...),
    current_user: User = Depends(get_current_user),
):
    """
    Accepts a resume file and pasted job description text.
    Analyze the resume against the job text and returns the full analysis.
    """
    file_path = await save_upload_file(file)

    try:
        raw_resume_text = extract_text(str(file_path))
        resume_data = extract_resume_data(raw_resume_text)
        raw_job_text = scrape_job_posting_fallback(job_text)
        job_data = extract_job_data(raw_job_text)
        analysis = analyze_resume_against_job(resume_data, job_data)

        return AnalyzeResponse(
            success = True,
            analysis_id = str(uuid.uuid4()),
            resume = resume_data,
            job = job_data,
            analysis = analysis,
            match_label = get_match_label(analysis.match_percentage),
            match_color = get_match_color(analysis.match_percentage),
        )
    except Exception as e:
        raise HTTPException(
            status_code = 500,
            detail = str(e)
        )
    finally:
        delete_file(file_path)


@router.post("/recommend", response_model = RecommendResponse)
async def get_recommendation(
    file : UploadFile = File(...),
    location : str = Form(default=""),
    employment_type : str = Form(default = "FULLTIME"),
    remote_only : bool = Form(default = False),
    current_user: User = Depends(get_current_user),
):
    """
    Accepts a resume file and search preferences.
    Searches multiple job portals automatically.
    Returns top 10 job recommendations ranked by match percentage.
    """

    file_path = await save_upload_file(file)

    try:
        raw_resume_text = extract_text(str(file_path))

        resume_data = extract_resume_data(raw_resume_text)

        preferences = SearchPreferences(
            location = location,
            employment_type = employment_type,
            remote_only = remote_only,
        )

        recommendations, search_query = await generate_recommendations(
            resume = resume_data,
            preferences = preferences,
            top_n = 10,
        )

        return RecommendResponse(
            success = True,
            resume = resume_data,
            total_jobs_found = len(recommendations),
            total_jobs_analyzed = len(recommendations),
            recommendation = recommendations,
            search_query = search_query,
            preferences = preferences,
        )
    
    except Exception as e:
        raise HTTPException(
            status_code = 500,
            detail = str(e)
        )
    
    finally:
        delete_file(file_path)


@router.post("/apply", response_model=ApplyResponse)
async def apply_for_job(
    file : UploadFile = File(...),
    job_url : str = Form(...),
    job_title : str = Form(default = ""),
    job_company : str = Form(default = ""),
    job_description : str = Form(default = ""),
    required_skills : str = Form(default = ""),
    current_user: User = Depends(get_current_user),
):
    """
    Accepts a resume file and job details.
    Generates a cover letter and pre-fills the job application form.
    Opens browser for user to review and submit.
    """

    file_path = await save_upload_file(file)

    try:
        raw_resume_text = extract_text(str(file_path))
        resume_data = extract_resume_data(raw_resume_text)
        job_data = extract_job_data(raw_resume_text) if not job_title else None

        from app.models.schemas import JobData
        if not job_data:
            job_data = JobData(
                title = job_title,
                company = job_company,
                description = job_description,
                required_skills = required_skills.split(',') if required_skills else [],
            )

        app_data_dict = build_application_data(resume_data, job_data) # building application data with cover letter refer cover_letter.py
        application_data = ApplicationData(**app_data_dict)

        import asyncio
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda : fill_job_application(job_url, application_data)
        )
        return response
    
    except Exception as e:
        raise HTTPException(
            status_code = 500,
            detail = str(e)
        )
    finally:
        delete_file(file_path)


@router.post("/apply/from-recommendation", response_model=ApplyResponse)
async def apply_from_recommendation(
    file: UploadFile = File(...),
    job_url: str = Form(...),
    job_title: str = Form(default=""),
    job_company: str = Form(default=""),
    job_description: str = Form(default=""),
    required_skills: str = Form(default=""),
    preferred_skills: str = Form(default=""),
    current_user: User = Depends(get_current_user),
):
    """
    Same as /apply but designed to be called directly
    from a job recommendation card in the UI.
    User clicks Apply on a recommendation and this endpoint handles it.
    """

    file_path = await save_upload_file(file)

    try:
        raw_resume_text = extract_text(str(file_path))
        resume_data = extract_resume_data(raw_resume_text)

        from app.models.schemas import JobData
        job_data = JobData(
            title=job_title,
            company=job_company,
            description=job_description,
            required_skills=required_skills.split(",") if required_skills else [],
            preferred_skills=preferred_skills.split(",") if preferred_skills else [],
        )

        app_data_dict = build_application_data(resume_data, job_data)
        application_data = ApplicationData(**app_data_dict)

        import asyncio
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: fill_job_application(job_url, application_data)
        )

        return response

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

    finally:
        delete_file(file_path)


@router.get("/health")
async def router_health():
    """
    Simple health check for the router.
    """
    return {"status" : "ok", "router" : "analyze"}

