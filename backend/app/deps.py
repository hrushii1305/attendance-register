"""Shared pieces every route can ask for: the Supabase client, the Store,
and the logged-in teacher."""
import logging
import os
from functools import lru_cache

from dotenv import load_dotenv
from fastapi import Depends, Header, HTTPException
from supabase import Client, create_client
from supabase_auth.errors import AuthError, AuthRetryableError

from app.store import Store

logger = logging.getLogger("uvicorn.error")  # shows up in the backend window


@lru_cache
def get_client() -> Client:
    """One Supabase client for the whole app, using the SECRET key from .env."""
    load_dotenv()
    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SECRET_KEY"])


def get_store(client: Client = Depends(get_client)) -> Store:
    return Store(client)


def require_user(
    authorization: str | None = Header(None),
    client: Client = Depends(get_client),
):
    """Check the 'Authorization: Bearer <token>' header with Supabase.
    Anything wrong (missing, wrong format, invalid or expired) -> 401."""
    scheme, _, token = (authorization or "").partition(" ")
    token = token.strip()
    if scheme != "Bearer" or not token:
        raise HTTPException(status_code=401, detail="Not logged in")
    try:
        user = client.auth.get_user(token).user
    except AuthRetryableError:
        # Network trouble: not the teacher's fault, so don't log them out.
        logger.exception("Could not reach Supabase to check the login token")
        raise HTTPException(status_code=503, detail="Can't reach Supabase right now. Try again.")
    except AuthError as e:
        # Supabase says the token is bad or expired. (If EVERY request lands here,
        # check SUPABASE_URL and SUPABASE_SECRET_KEY in backend/.env.)
        logger.warning("Login token rejected by Supabase: %s", e)
        user = None
    except Exception:
        logger.exception("Unexpected error while checking the login token")
        raise HTTPException(
            status_code=503,
            detail="Couldn't check your login with Supabase. Check the backend window and backend/.env.",
        )
    if not user:
        raise HTTPException(status_code=401, detail="Not logged in")
    return user
