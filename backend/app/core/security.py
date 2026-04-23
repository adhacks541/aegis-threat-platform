"""
JWT issuance & FastAPI dependency guard.

Usage
-----
Protected route:
    @router.get("/protected")
    async def protected(user: dict = Depends(get_current_user)):
        ...

Optional (returns None if no token):
    @router.get("/maybe-protected")
    async def maybe(user: dict = Depends(get_current_user_optional)):
        ...
"""
from datetime import datetime, timedelta, timezone
from typing import Optional
import time

import requests as _requests
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/token")
oauth2_scheme_optional = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/token", auto_error=False
)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def get_password_hash(plain: str) -> str:
    return pwd_context.hash(plain)


# ---------------------------------------------------------------------------
# Clerk JWT verification (JWKS-based RS256)
# ---------------------------------------------------------------------------
_jwks_cache: dict = {"keys": [], "fetched_at": 0.0}
_JWKS_TTL = 300  # re-fetch every 5 minutes


def _get_clerk_jwks() -> list:
    """Return cached JWKS keys, refreshing if stale."""
    now = time.time()
    if now - _jwks_cache["fetched_at"] > _JWKS_TTL or not _jwks_cache["keys"]:
        try:
            resp = _requests.get(settings.CLERK_JWKS_URL, timeout=5)
            resp.raise_for_status()
            _jwks_cache["keys"] = resp.json().get("keys", [])
            _jwks_cache["fetched_at"] = now
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Could not fetch Clerk JWKS: {exc}",
            )
    return _jwks_cache["keys"]


def verify_clerk_token(token: str) -> dict:
    """
    Verify a Clerk-issued JWT against Clerk's JWKS endpoint.
    Returns the decoded payload with user info (sub = Clerk user ID).
    """
    try:
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Clerk token header: {exc}",
        )

    keys = _get_clerk_jwks()
    key = next((k for k in keys if k.get("kid") == kid), None)
    if key is None:
        # kid not found — force refresh and retry once
        _jwks_cache["fetched_at"] = 0.0
        keys = _get_clerk_jwks()
        key = next((k for k in keys if k.get("kid") == kid), None)

    if key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Clerk signing key not found",
        )

    try:
        payload = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            options={"verify_aud": False},  # Clerk doesn't require aud claim
        )
        return payload
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Clerk token invalid: {exc}",
        )


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])


# ---------------------------------------------------------------------------
# FastAPI dependencies
# ---------------------------------------------------------------------------

CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    try:
        payload = decode_token(token)
        username: str | None = payload.get("sub")
        if not username:
            raise CREDENTIALS_EXCEPTION
        return {"username": username}
    except JWTError:
        raise CREDENTIALS_EXCEPTION


async def get_current_user_optional(
    token: str | None = Depends(oauth2_scheme_optional),
) -> dict | None:
    if not token:
        return None
    try:
        payload = decode_token(token)
        username: str | None = payload.get("sub")
        if username:
            return {"username": username}
    except JWTError:
        pass
    return None
