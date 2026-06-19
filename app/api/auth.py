# app/api/auth.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import User
from app.auth.utils import hash_password, verify_password, create_access_token
from app.api.dependencies import get_current_user
from app.models.schemas import SignupRequest, LoginRequest, TokenResponse, UserResponse

router = APIRouter()


# ─── Signup ───────────────────────────────────────────────────────────────────

@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    """
    Register a new user account.
    - Checks if email is already taken
    - Hashes the password with bcrypt
    - Creates the user in the database
    - Returns a JWT token immediately (auto-login after signup)
    """

    # Check if a user with this email already exists
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists.",
        )

    # Create and save the new user
    new_user = User(
        name=payload.name,
        email=payload.email,
        hashed_password=hash_password(payload.password),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)  # loads the auto-generated id and timestamps

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

    # Generate fresh JWT token
    token = create_access_token(data={"sub": user.email})

    return TokenResponse(
        access_token=token,
        user_id=user.id,
        name=user.name,
        email=user.email,
    )


# ─── Get Current User ─────────────────────────────────────────────────────────

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """
    Returns the profile of the currently logged-in user.
    Requires a valid Bearer token in the Authorization header.
    """
    return current_user
