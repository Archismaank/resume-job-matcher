import asyncio
import uuid
import traceback
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from app.api.file_handler import save_upload_file, delete_file
from app.api.dependencies import get_current_user
from app.db.database import get_db
from app.db.models import User, AnalysisHistory, RecommendationHistory
from app.parsers.resume import extract_text
from app.parsers.job_scraper import scrape_job_posting, scrape_job_posting_fallback
from app.agents.analyzer import extract_resume_data, extract_job_data, analyze_resume_against_job
from app.agents.scorer import get_match_label, get_match_color
from app.agents.recommender import generate_recommendations
from app.models.schemas import (
    AnalyzeResponse, RecommendResponse, SearchPreferences,
    AnalysisHistoryResponse, RecommendationHistoryResponse
)
# APIRouter -> it's like a mini app and we define routes here and register them in main.py
router = APIRouter()

@router.post("/analyze/url", response_model = AnalyzeResponse)
async def analyze_with_url(
    file : UploadFile = File(...),
    job_url : str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Accepts a resume file and job posting url.
    Scrapes the job URL, analyze the resume against it, and returns the full analysis.
    """

    # save the uploaded file
    file_path = await save_upload_file(file)

    try:
        print("[analyze/url] Step 1: extracting resume text...")
        raw_resume_text = extract_text(str(file_path))

        print("[analyze/url] Step 2: parsing resume with AI...")
        resume_data = extract_resume_data(raw_resume_text)

        print("[analyze/url] Step 3: scraping job URL...")
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

        print("[analyze/url] Step 4: extracting job data with AI...")
        job_data = extract_job_data(raw_job_text)

        print("[analyze/url] Step 5: analyzing resume vs job...")
        analysis = analyze_resume_against_job(resume_data, job_data)

        print("[analyze/url] Step 6: building response...")
        response = AnalyzeResponse(
            success = True,
            analysis_id = str(uuid.uuid4()),
            resume = resume_data,
            job = job_data,
            analysis = analysis,
            match_label = get_match_label(analysis.match_percentage),
            match_color = get_match_color(analysis.match_percentage),
        )

        # Save to history
        history_record = AnalysisHistory(
            user_id=current_user.id,
            job_title=job_data.title,
            company=job_data.company,
            job_url=job_url,
            match_percentage=analysis.match_percentage,
            full_result_json=response.model_dump_json(),
        )
        db.add(history_record)
        db.commit()

        return response
    except HTTPException:
        raise  # pass-through 422 and other intentional HTTP errors
    except Exception as e:
        print(f"[analyze/url] ERROR: {e}")
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
    db: Session = Depends(get_db),
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

        response = AnalyzeResponse(
            success = True,
            analysis_id = str(uuid.uuid4()),
            resume = resume_data,
            job = job_data,
            analysis = analysis,
            match_label = get_match_label(analysis.match_percentage),
            match_color = get_match_color(analysis.match_percentage),
        )

        history_record = AnalysisHistory(
            user_id=current_user.id,
            job_title=job_data.title,
            company=job_data.company,
            job_url=None,
            match_percentage=analysis.match_percentage,
            full_result_json=response.model_dump_json(),
        )
        db.add(history_record)
        db.commit()

        return response
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
    db: Session = Depends(get_db),
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

        response = RecommendResponse(
            success = True,
            resume = resume_data,
            total_jobs_found = len(recommendations),
            total_jobs_analyzed = len(recommendations),
            recommendation = recommendations,
            search_query = search_query,
            preferences = preferences,
        )

        history_record = RecommendationHistory(
            user_id=current_user.id,
            search_query=search_query,
            total_jobs_found=len(recommendations),
            full_result_json=response.model_dump_json(),
        )
        db.add(history_record)
        db.commit()

        return response
    
    except Exception as e:
        raise HTTPException(
            status_code = 500,
            detail = str(e)
        )
    
    finally:
        delete_file(file_path)



@router.get("/health")
async def router_health():
    """
    Simple health check for the router.
    """
    return {"status" : "ok", "router" : "analyze"}


@router.get("/history/analyses", response_model=list[AnalysisHistoryResponse])
async def get_analysis_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Fetch past analyses for the logged-in user."""
    analyses = (
        db.query(AnalysisHistory)
        .filter(AnalysisHistory.user_id == current_user.id)
        .order_by(AnalysisHistory.created_at.desc())
        .all()
    )
    # The 'created_at' field is a datetime object, but pydantic schema expects string (or datetime will serialize to string)
    # Actually Pydantic will cast datetime to str automatically, so it's fine.
    return analyses


@router.get("/history/recommendations", response_model=list[RecommendationHistoryResponse])
async def get_recommendation_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Fetch past job recommendations for the logged-in user."""
    recs = (
        db.query(RecommendationHistory)
        .filter(RecommendationHistory.user_id == current_user.id)
        .order_by(RecommendationHistory.created_at.desc())
        .all()
    )
    return recs


@router.delete("/history/analyses/{analysis_id}")
async def delete_analysis_history(
    analysis_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a specific analysis history entry."""
    record = db.query(AnalysisHistory).filter(
        AnalysisHistory.id == analysis_id,
        AnalysisHistory.user_id == current_user.id,
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="Analysis not found.")
    db.delete(record)
    db.commit()
    return {"success": True, "message": "Analysis deleted."}


@router.delete("/history/recommendations/{rec_id}")
async def delete_recommendation_history(
    rec_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a specific recommendation history entry."""
    record = db.query(RecommendationHistory).filter(
        RecommendationHistory.id == rec_id,
        RecommendationHistory.user_id == current_user.id,
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="Recommendation not found.")
    db.delete(record)
    db.commit()
    return {"success": True, "message": "Recommendation deleted."}
