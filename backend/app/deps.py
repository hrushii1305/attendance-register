"""Shared pieces every route can ask for: the Supabase client, the Store,
and the logged-in teacher."""
import os
from functools import lru_cache

from dotenv import load_dotenv
from fastapi import Depends, Header, HTTPException
from supabase import Client, create_client

from app.store import Store


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
    except Exception:
        user = None
    if not user:
        raise HTTPException(status_code=401, detail="Not logged in")
    return user
