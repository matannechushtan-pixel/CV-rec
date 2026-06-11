from fastapi import APIRouter, Depends
from core.auth import require_company_admin

router = APIRouter()


@router.post("/jobs", status_code=501)
async def create_job(_user: dict = Depends(require_company_admin)):
    return {"detail": "Not implemented — Phase 8"}


@router.get("/jobs")
async def list_jobs(_user: dict = Depends(require_company_admin)):
    return {"detail": "Not implemented — Phase 8"}


@router.get("/jobs/{job_id}/candidates")
async def get_candidates(job_id: str, _user: dict = Depends(require_company_admin)):
    return {"detail": "Not implemented — Phase 8"}


@router.get("/candidates/{candidate_id}")
async def get_candidate(candidate_id: str, _user: dict = Depends(require_company_admin)):
    return {"detail": "Not implemented — Phase 8"}
