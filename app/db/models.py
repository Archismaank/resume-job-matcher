
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class User(Base):
    """
    Represents a registered user in the system.
    """
    __tablename__ = "users"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Core identity
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    # Optional profile fields (filled from resume or manually)
    phone = Column(String, default="")
    linkedin_url = Column(String, default="")
    github_url = Column(String, default="")
    portfolio_url = Column(String, default="")

    # Email verification
    is_verified = Column(Boolean, default=False)
    verification_token = Column(String, nullable=True)
    verification_token_expires = Column(DateTime(timezone=True), nullable=True)

    # Password reset
    reset_token = Column(String, nullable=True)
    reset_token_expires = Column(DateTime(timezone=True), nullable=True)

    # Account status
    is_active = Column(Boolean, default=True)

    # Automatic timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    analyses = relationship("AnalysisHistory", back_populates="user", cascade="all, delete-orphan")
    recommendations = relationship("RecommendationHistory", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User id={self.id} email='{self.email}'>"


class AnalysisHistory(Base):
    """
    Stores past resume-vs-job analyses.
    """
    __tablename__ = "analysis_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    job_title = Column(String, nullable=False)
    company = Column(String, nullable=False)
    job_url = Column(String, nullable=True)
    match_percentage = Column(Float, nullable=False)
    
    # Store the entire AnalyzeResponse JSON as a string
    full_result_json = Column(Text, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="analyses")


class RecommendationHistory(Base):
    """
    Stores past multi-portal job search results.
    """
    __tablename__ = "recommendation_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    search_query = Column(String, nullable=False)
    total_jobs_found = Column(Integer, default=0)
    
    # Store the entire RecommendResponse JSON as a string
    full_result_json = Column(Text, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="recommendations")
