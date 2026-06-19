
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import User
from app.auth.utils import decode_access_token

# Tells FastAPI to look for: Authorization: Bearer <token> in request headers
# auto_error=False means we handle the error ourselves with a cleaner message
bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Reusable FastAPI dependency for protected routes.

    What it does:
    1. Extracts the JWT from the Authorization: Bearer <token> header
    2. Decodes and validates the token signature + expiry
    3. Pulls the user email out of the token payload
    4. Looks up and returns the User from the database
    5. Raises HTTP 401 if anything is wrong

    Usage in any route:
        @router.get("/protected")
        def protected_route(user: User = Depends(get_current_user)):
            return {"hello": user.name}
    """

    # No token provided at all
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated. Please log in.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    # Decode and validate the JWT
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is invalid or has expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract the user's email from the token payload ("sub" = subject)
    email: str = payload.get("sub")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload is malformed.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Look up the user in the database
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account not found. It may have been deleted.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check the account is still active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been deactivated.",
        )

    return user  # the actual SQLAlchemy User object
