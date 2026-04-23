from fastapi import APIRouter, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import Depends

from app.core.config import settings
from app.core.security import verify_password, create_access_token, verify_clerk_token

router = APIRouter()


@router.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    OAuth2 password flow — returns a Bearer JWT.
    POST form fields: username, password
    """
    if form_data.username != settings.ADMIN_USERNAME:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not verify_password(form_data.password, settings.ADMIN_PASSWORD_HASH):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(data={"sub": form_data.username})
    return {"access_token": token, "token_type": "bearer"}


@router.post("/clerk")
async def clerk_token_exchange(request: Request):
    """
    Clerk token exchange — verifies a Clerk-issued JWT and returns
    an internal backend JWT. The frontend calls this once after Clerk
    sign-in; all subsequent API calls use the returned internal token.
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Bearer token",
        )

    clerk_token = auth_header.removeprefix("Bearer ").strip()

    # Verify against Clerk's JWKS — raises HTTPException on failure
    payload = verify_clerk_token(clerk_token)

    # Use Clerk user ID as the subject in our internal JWT
    clerk_user_id = payload.get("sub", "clerk_user")
    email = payload.get("email", "")

    internal_token = create_access_token(
        data={"sub": clerk_user_id, "email": email, "provider": "clerk"}
    )
    return {"access_token": internal_token, "token_type": "bearer"}

