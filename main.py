# main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.api.routes import router as analyze_router
from app.api.auth import router as auth_router
from app.db.database import create_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create all database tables on startup (safe — only creates if not existing)
    create_tables()
    print(f"Starting Resume Job Matcher...")
    print(f"Environment: {settings.app_env}")
    print(f"AI Provider: {settings.ai_provider}")

    yield  # Server is running and accepting requests

    # This runs once when the server shuts down
    print("Shutting down...")


# Create the FastAPI app
app = FastAPI(
    title="Resume Job Matcher API",
    description="Upload your resume, paste a job URL, get a match score and skill gap analysis.",
    version="0.1.0",
    lifespan=lifespan,
)

# This allows our Streamlit frontend to talk to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register the analyze router
# All routes in routes.py will be prefixed with /api/v1
app.include_router(
    analyze_router,
    prefix = "/api/v1",
    tags = ["Analysis"]
)

# Register the auth router — /api/v1/auth/signup, /api/v1/auth/login, etc.
app.include_router(
    auth_router,
    prefix="/api/v1/auth",
    tags=["Auth"],
)

@app.get("/")
async def root():
    # This is the home route
    return {
        "message": "Resume Job Matcher API is running.",
        "docs": "Visit /docs to explore the API",
        "version" : "1.0.0"
    }


@app.get("/health")
async def health_check():
    # This route checks if the server is running correctly
    return {
        "status": "ok",
        "environment": settings.app_env,
        "ai_provider": settings.ai_provider,
    }