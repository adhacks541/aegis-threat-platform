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
    Clerk token exchange — production-grade flow:
    1. Verify the Clerk JWT via JWKS
    2. Fetch the user's verified primary email via Clerk Backend API
    3. Check email against ALLOWED_EMAILS allowlist (if configured)
    4. Issue an internal backend JWT on success
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Bearer token",
        )

    clerk_token = auth_header.removeprefix("Bearer ").strip()

    # Step 1: Verify Clerk JWT signature
    payload = verify_clerk_token(clerk_token)
    clerk_user_id = payload.get("sub", "")

    if not clerk_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Clerk token: missing sub",
        )

    # Step 2: Fetch user profile from Clerk Backend API (authoritative email source)
    email = ""
    if settings.CLERK_SECRET_KEY:
        try:
            import requests as _req
            resp = _req.get(
                f"https://api.clerk.com/v1/users/{clerk_user_id}",
                headers={"Authorization": f"Bearer {settings.CLERK_SECRET_KEY}"},
                timeout=5,
            )
            if resp.ok:
                user_data = resp.json()
                primary_email_id = user_data.get("primary_email_address_id")
                for addr in user_data.get("email_addresses", []):
                    if addr.get("id") == primary_email_id:
                        email = addr.get("email_address", "")
                        break
        except Exception:
            pass  # If Clerk API is unreachable, fall back to JWT claims
        email = email or payload.get("email", "")
    else:
        email = payload.get("email", "")

    # Step 3: Enforce allowlist
    allowed_raw = settings.ALLOWED_EMAILS.strip()
    if allowed_raw:
        allowed = {e.strip().lower() for e in allowed_raw.split(",") if e.strip()}
        if email.lower() not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: {email} is not authorised",
            )

    # Step 4: Issue internal JWT
    internal_token = create_access_token(
        data={"sub": clerk_user_id, "email": email, "provider": "clerk"}
    )
    return {"access_token": internal_token, "token_type": "bearer", "email": email}


