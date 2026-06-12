"""Site generation routes — canonical site_builder.py (Phase 4)."""

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(tags=["build"])


class BuildSiteRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    location: str = Field(min_length=2, max_length=100)
    website: Optional[str] = None
    business_type: Optional[str] = None
    deploy: bool = False
    lead_tier: str = "WARM"


@router.post("/build-site")
def build_site(req: BuildSiteRequest):
    """Generate demo site HTML via site_builder.py (canonical generator)."""
    try:
        from site_builder import build_site_for_api

        result = build_site_for_api(
            req.name,
            req.location,
            website=req.website or "",
            business_type=req.business_type or "",
            deploy=req.deploy,
            lead_tier=req.lead_tier,
        )
        if not result.get("html"):
            raise HTTPException(status_code=500, detail="Site build produced empty HTML")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))