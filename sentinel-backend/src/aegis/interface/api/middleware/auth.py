"""Clerk JWT authentication via manual JWKS verification (python-jose + httpx).

This module exposes two FastAPI dependencies:
  - get_current_user: requires a valid JWT, raises 401 if absent or invalid.
  - get_optional_user: returns None instead of raising if auth is missing.

We validate tokens against Clerk's JWKS endpoint without using the Clerk SDK,
keeping the dependency footprint minimal and the verification logic transparent.
"""

import logging
from typing import Optional

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from aegis.config import settings

logger = logging.getLogger(__name__)

# In-memory JWKS cache. Populated on first token validation, cleared on key mismatch
# (to handle key rotation automatically).
_jwks_cache: Optional[dict] = None


async def _fetch_jwks() -> dict:
    """Fetch the JWKS from Clerk's JWKS endpoint, using the in-memory cache.

    The cache is intentionally module-level so it persists across requests
    within a single process lifetime. This avoids hitting the JWKS endpoint
    on every request.
    """
    global _jwks_cache
    if _jwks_cache is not None:
        return _jwks_cache

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(settings.clerk_jwks_url)
        response.raise_for_status()
        _jwks_cache = response.json()
        logger.info("JWKS fetched and cached from %s", settings.clerk_jwks_url)
        return _jwks_cache


def _find_rsa_key(jwks: dict, kid: str) -> Optional[dict]:
    """Return the JWK entry matching the given key ID, or None."""
    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            return {
                "kty": key["kty"],
                "kid": key["kid"],
                "use": key.get("use", "sig"),
                "n": key["n"],
                "e": key["e"],
            }
    return None


async def verify_clerk_jwt(token: str) -> dict:
    """Verify a Clerk-issued JWT and return the decoded payload.

    Steps:
      1. Decode the JWT header (unverified) to extract the key ID.
      2. Fetch the JWKS and locate the matching RSA public key.
      3. If the key is not found, clear the cache (key rotation) and retry once.
      4. Verify the JWT signature with python-jose using RS256.
      5. Return the verified payload dict.

    Raises HTTPException 401 on any verification failure.
    """
    global _jwks_cache

    try:
        unverified_header = jwt.get_unverified_header(token)
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed token header",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    kid = unverified_header.get("kid")
    if not kid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is missing key ID (kid)",
            headers={"WWW-Authenticate": "Bearer"},
        )

    jwks = await _fetch_jwks()
    rsa_key = _find_rsa_key(jwks, kid)

    if rsa_key is None:
        # The key wasn't found — Clerk may have rotated keys. Clear cache and retry.
        logger.warning("Signing key %s not found in JWKS cache; refreshing.", kid)
        _jwks_cache = None
        jwks = await _fetch_jwks()
        rsa_key = _find_rsa_key(jwks, kid)

    if rsa_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No matching signing key found for this token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload: dict = jwt.decode(
            token,
            rsa_key,
            algorithms=["RS256"],
            # Clerk tokens use the frontend API URL as the audience,
            # which varies per instance. We skip audience validation here
            # and rely on signature + expiry verification instead.
            options={"verify_aud": False},
        )
        return payload
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token validation failed: {exc}",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


# HTTPBearer scheme — auto_error=False so we can return a clean error ourselves.
_bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
) -> str:
    """FastAPI dependency: requires a valid Clerk JWT.

    Returns the Clerk user ID (sub claim) on success.
    Raises HTTP 401 if the header is absent or the token is invalid.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header is required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = await verify_clerk_jwt(credentials.credentials)

    clerk_id: Optional[str] = payload.get("sub")
    if not clerk_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is missing subject claim",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return clerk_id


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
) -> Optional[str]:
    """FastAPI dependency: optionally validates a Clerk JWT.

    Returns the Clerk user ID on success, or None if no token is provided.
    Still raises HTTP 401 if a token is present but invalid.
    """
    if credentials is None:
        return None

    payload = await verify_clerk_jwt(credentials.credentials)
    return payload.get("sub")
