"""LLM (Azure AI Foundry) diagnostics + info endpoints."""
from __future__ import annotations
from fastapi import APIRouter, HTTPException

from src.app.deps import get_deps

router = APIRouter(prefix="/llm", tags=["llm"])


@router.get("/info")
async def info() -> dict:
    """Current LLM wiring (no secrets) — handy to confirm what the API will call."""
    s = get_deps().settings
    return {
        "enabled": s.llm_enabled,
        "endpoint": s.aoai_endpoint,
        "deployment": s.aoai_deployment,
        "apiVersion": s.aoai_api_version,
        "authMode": "api_key" if s.aoai_api_key else "entra_id",
    }


@router.get("/health")
async def health() -> dict:
    """Live round-trip to the model — verifies the endpoint, key, and deployment."""
    s = get_deps().settings
    if not s.llm_enabled:
        return {"enabled": False, "ok": False, "detail": "WC_LLM_ENABLED is false"}
    try:
        text = await get_deps().llm.complete(
            "Reply with exactly one word: pong", seed_key="diagnostics:ping")
    except Exception as e:  # surface the real provider error to the caller
        raise HTTPException(status_code=502, detail=f"{type(e).__name__}: {e}")
    return {"enabled": True, "ok": bool(text), "deployment": s.aoai_deployment,
            "sample": text[:200]}
