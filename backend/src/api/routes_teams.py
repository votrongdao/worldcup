"""Team + squad endpoints.

Teams are generated per tournament and live under the tournament aggregate, so use
``GET /tournaments/{id}/teams`` for the roster. A global team lookup needs a
team -> tournament index that is not modelled yet.
"""
from __future__ import annotations
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/teams", tags=["teams"])


@router.get("/{team_id}")
async def get_team(team_id: str):
    raise HTTPException(status_code=501,
                        detail="use GET /tournaments/{id}/teams")
