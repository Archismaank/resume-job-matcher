# app/api/auth.py

import uuid
import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import User
from app.auth.utils import hash_password, verify_password, create_access_token
from app.api.dependencies import get_current_user
from app.config import settings
from app.email.mailer import send_verification_email, send_password_reset_email
from app.models.schemas import (
    SignupRequest, LoginRequest, TokenResponse, UserResponse, UpdateProfileRequest,
    ForgotPasswordRequest, ResetPasswordRequest
)

router = APIRouter()
logger = logging.getLogger(__name__)


# ─── Signup ───────────────────────────────────────────────────────────────────

@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    """
    Register a new user account.
    - Checks if email is already taken
    - Hashes the password with bcrypt
    - Creates the user in the database
    - Sends a verification email (if SMTP configured)
    - Returns a JWT token immediately (auto-login after signup)
    """

    # Check if a user with this email already exists
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists.",
        )

    # Generate a short-lived verification token (24 hours)
    verification_token = str(uuid.uuid4())
    token_expiry = datetime.now(timezone.utc) + timedelta(hours=24)

    # Create and save the new user
    new_user = User(
        name=payload.name,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        # If verification is disabled, mark as verified immediately
        is_verified=not settings.email_verification_enabled,
        verification_token=verification_token if settings.email_verification_enabled else None,
        verification_token_expires=token_expiry if settings.email_verification_enabled else None,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Send verification email (non-blocking — app still works if it fails)
    if settings.email_verification_enabled:
        sent = send_verification_email(new_user.email, new_user.name, verification_token)
        if not sent:
            logger.warning(f"Could not send verification email to {new_user.email}")

    # Generate JWT token so user is logged in right away
    token = create_access_token(data={"sub": new_user.email})

    return TokenResponse(
        access_token=token,
        user_id=new_user.id,
        name=new_user.name,
        email=new_user.email,
    )


# ─── Login ────────────────────────────────────────────────────────────────────

@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """
    Log in with email and password.
    - Looks up user by email
    - Verifies the password against the stored bcrypt hash
    - Blocks unverified users if verification is enabled
    - Returns a fresh JWT token on success
    """

    # Find user by email
    user = db.query(User).filter(User.email == payload.email).first()

    # Use a generic error so attackers can't tell if the email exists
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been deactivated.",
        )

    # Block login if email not verified (only when verification is enabled)
    if settings.email_verification_enabled and not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="EMAIL_NOT_VERIFIED",
        )

    # Generate fresh JWT token
    token = create_access_token(data={"sub": user.email})

    return TokenResponse(
        access_token=token,
        user_id=user.id,
        name=user.name,
        email=user.email,
    )


# ─── Verify Email ─────────────────────────────────────────────────────────────

@router.get("/verify-email")
def verify_email(token: str = Query(...), db: Session = Depends(get_db)):
    """
    Verifies a user's email address using the token from the email link.
    Marks the user as verified and clears the token.
    """
    user = db.query(User).filter(User.verification_token == token).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or already-used verification link.",
        )

    # Check expiry
    if user.verification_token_expires:
        expires = user.verification_token_expires
        # Make naive datetimes timezone-aware for comparison
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) > expires:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Verification link has expired. Please request a new one.",
            )

    user.is_verified = True
    user.verification_token = None
    user.verification_token_expires = None
    db.commit()

    return {"message": "Email verified successfully! You can now log in."}


# ─── Resend Verification Email ────────────────────────────────────────────────

@router.post("/resend-verification")
def resend_verification(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Resends the verification email to the currently logged-in (but unverified) user.
    """
    if current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Your email is already verified.",
        )

    if not settings.email_verification_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email verification is not enabled.",
        )

    # Generate a fresh token
    new_token = str(uuid.uuid4())
    current_user.verification_token = new_token
    current_user.verification_token_expires = datetime.now(timezone.utc) + timedelta(hours=24)
    db.commit()

    sent = send_verification_email(current_user.email, current_user.name, new_token)
    if not sent:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification email. Please check your SMTP settings.",
        )

    return {"message": "Verification email resent. Please check your inbox."}


# ─── Get Current User ─────────────────────────────────────────────────────────

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """
    Returns the profile of the currently logged-in user.
    Requires a valid Bearer token in the Authorization header.
    """
    return current_user


# ─── Update Profile ───────────────────────────────────────────────────────────

@router.put("/profile", response_model=UserResponse)
def update_profile(
    payload: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update the current user's profile fields.
    Only updates fields that are provided (non-None).
    """
    if payload.name is not None:
        current_user.name = payload.name
    if payload.phone is not None:
        current_user.phone = payload.phone
    if payload.linkedin_url is not None:
        current_user.linkedin_url = payload.linkedin_url
    if payload.github_url is not None:
        current_user.github_url = payload.github_url
    if payload.portfolio_url is not None:
        current_user.portfolio_url = payload.portfolio_url

    db.commit()
    db.refresh(current_user)
    return current_user


# ─── Password Reset ───────────────────────────────────────────────────────────

@router.post("/forgot-password")
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """
    Initiates the password reset flow.
    If the email exists, generates a reset token and sends a reset email.
    Always returns a generic success message to prevent email enumeration.
    """
    user = db.query(User).filter(User.email == payload.email).first()

    if user:
        # Generate token and set expiry to 1 hour
        reset_token = str(uuid.uuid4())
        token_expiry = datetime.now(timezone.utc) + timedelta(hours=1)

        user.reset_token = reset_token
        user.reset_token_expires = token_expiry
        db.commit()

        # Send email
        send_password_reset_email(user.email, user.name, reset_token)

    return {"message": "If that email exists in our system, a password reset link has been sent."}


@router.post("/reset-password")
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    """
    Resets the user's password using the provided token.
    """
    user = db.query(User).filter(User.reset_token == payload.token).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or already-used reset link.",
        )

    # Check expiry
    if user.reset_token_expires:
        expires = user.reset_token_expires
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) > expires:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password reset link has expired. Please request a new one.",
            )

    # Update password and clear token
    user.hashed_password = hash_password(payload.new_password)
    user.reset_token = None
    user.reset_token_expires = None
    db.commit()

    return {"message": "Your password has been successfully reset. You can now log in."}
