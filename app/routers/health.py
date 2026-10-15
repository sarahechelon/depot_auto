"""GET /health endpoint."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    """Return a static health response."""
    return {"status": "ok"}
