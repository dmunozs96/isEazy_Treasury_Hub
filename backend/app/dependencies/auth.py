from fastapi import Header, HTTPException


async def get_current_user(x_api_key: str | None = Header(default=None)) -> str:
    """Phase 1: minimal API key auth. Returns a user identifier string."""
    if x_api_key is None:
        return "system"
    return x_api_key
