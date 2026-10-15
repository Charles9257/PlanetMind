from fastapi import APIRouter

router = APIRouter(prefix="/api/v1", tags=["health"])


@router.get("/health")
def healthcheck() -> dict:
    return {"status": "ok", "service": "planetmind-backend"}
