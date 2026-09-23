"""Supabase Authentication Verification & RBAC Authorization Module for FastAPI.

Validates Supabase JWT tokens using Supabase JWKS (ES256 Asymmetric Verification),
resolves Supabase Auth User UUID (auth_user_id), and synchronizes local PostgreSQL user records.
"""

import logging
import os
from typing import Dict, List, Optional
import jwt
from jwt import PyJWKClient

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from deployment.database import (
    HealthProfile,
    User,
    UserProfile,
    UserPreference,
    get_db,
)

logger = logging.getLogger(__name__)

# Security scheme for FastAPI OpenAPI docs
security_scheme = HTTPBearer(auto_error=False)

# Cache PyJWKClient instances per SUPABASE_URL
_jwks_clients: Dict[str, PyJWKClient] = {}


def get_jwks_client(supabase_url: str) -> PyJWKClient:
    """Returns or instantiates a cached PyJWKClient for the given Supabase URL."""
    base_url = supabase_url.rstrip("/")
    if base_url not in _jwks_clients:
        jwks_url = f"{base_url}/auth/v1/.well-known/jwks.json"
        _jwks_clients[base_url] = PyJWKClient(
            jwks_url,
            cache_keys=True,
            cache_jwk_set=True,
            lifespan=300,  # 5-minute JWKS set cache lifespan
        )
    return _jwks_clients[base_url]


def decode_supabase_jwt(token: str) -> Dict[str, any]:
    """Decodes and cryptographically validates a Supabase ES256 JWT using JWKS.
    
    SECURITY MANDATE:
    - NEVER accepts unverified tokens (no fallback, signature verification required).
    - Requires SUPABASE_URL configured in environment (fails closed if missing).
    - Fetches/caches public EC JWKs from https://<PROJECT_REF>.supabase.co/auth/v1/.well-known/jwks.json
    - Enforces ES256 algorithm verification (legacy HS256 prohibited).
    - Enforces issuer == 'https://<PROJECT_REF>.supabase.co/auth/v1'
    - Enforces audience == 'authenticated'
    - Enforces expiration ('exp').
    - Extracts authoritative user UUID from the 'sub' claim.
    """
    supabase_url = os.getenv("SUPABASE_URL", "").strip()
    if not supabase_url:
        logger.error("SUPABASE_URL environment variable is unconfigured or empty.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed: server configuration error (missing SUPABASE_URL).",
        )

    base_url = supabase_url.rstrip("/")
    expected_issuer = f"{base_url}/auth/v1"

    try:
        jwks_client = get_jwks_client(base_url)
        signing_key = jwks_client.get_signing_key_from_jwt(token)

        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["ES256"],
            audience="authenticated",
            issuer=expected_issuer,
            options={"require": ["exp", "sub", "iss", "aud"]},
        )

        sub = payload.get("sub")
        if not sub:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Supabase token: missing 'sub' claim (User UUID)",
            )
        return payload

    except jwt.PyJWKClientError as e:
        logger.warning(f"JWKS key lookup failed for JWT token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Supabase token: unknown key ID (kid) or JWKS fetch failure ({str(e)})",
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Supabase authentication token has expired",
        )
    except jwt.InvalidIssuerError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Supabase token issuer (must be {expected_issuer})",
        )
    except jwt.InvalidAudienceError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Supabase token audience (must be 'authenticated')",
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Supabase token: {str(e)}",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected JWT verification exception: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}",
        )


def sync_local_user(
    db: Session,
    auth_user_id: str,
    email: Optional[str] = None,
    full_name: Optional[str] = None,
    role: str = "patient",
) -> User:
    """Finds or creates a local PostgreSQL User record mapped to the Supabase Auth UUID."""
    user = db.query(User).filter(User.auth_user_id == auth_user_id).first()

    if not user:
        logger.info(f"Creating local PostgreSQL user for Supabase auth_user_id: {auth_user_id}")
        user = User(
            auth_user_id=auth_user_id,
            email=email,
            full_name=full_name,
            role=role if role in ["patient", "clinician", "admin"] else "patient",
        )
        db.add(user)
        db.flush()

        # Initialize default user profile
        profile = UserProfile(user_id=user.id)
        db.add(profile)

        # Initialize default CDSS health profile
        health = HealthProfile(user_id=user.id)
        db.add(health)

        # Initialize default preferences
        pref = UserPreference(user_id=user.id)
        db.add(pref)

        try:
            db.commit()
            db.refresh(user)
        except Exception as err:
            db.rollback()
            logger.error(f"Error persisting user sync record: {err}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to initialize local user record",
            )
    else:
        # Update email/name if changed in Supabase
        updated = False
        if email and user.email != email:
            user.email = email
            updated = True
        if full_name and user.full_name != full_name:
            user.full_name = full_name
            updated = True
        if updated:
            try:
                db.commit()
                db.refresh(user)
            except Exception:
                db.rollback()

    return user


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: Session = Depends(get_db),
) -> User:
    """FastAPI dependency requiring a valid Supabase ES256 Bearer JWT token."""
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please provide a valid Supabase Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_supabase_jwt(credentials.credentials)
    auth_user_id = payload["sub"]
    email = payload.get("email")
    user_metadata = payload.get("user_metadata", {})
    full_name = user_metadata.get("full_name") or user_metadata.get("name")
    role = user_metadata.get("role", "patient")

    user = sync_local_user(db, auth_user_id, email=email, full_name=full_name, role=role)

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account has been deactivated",
        )

    return user


def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """FastAPI dependency for optional authentication. Returns User or None."""
    if not credentials or not credentials.credentials:
        return None

    try:
        payload = decode_supabase_jwt(credentials.credentials)
        auth_user_id = payload["sub"]
        email = payload.get("email")
        user_metadata = payload.get("user_metadata", {})
        full_name = user_metadata.get("full_name") or user_metadata.get("name")
        role = user_metadata.get("role", "patient")

        return sync_local_user(db, auth_user_id, email=email, full_name=full_name, role=role)
    except Exception:
        return None


class RoleChecker:
    """Role-based access control (RBAC) authorization checker dependency."""

    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, user: User = Depends(get_current_user)) -> User:
        if user.role not in self.allowed_roles and user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Requires role: {', '.join(self.allowed_roles)} (Current role: {user.role})",
            )
        return user
