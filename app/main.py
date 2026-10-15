"""Application factory for Depot."""

from fastapi import FastAPI

from app.routers import health, products


def create_app() -> FastAPI:
    """Build and configure the FastAPI app."""
    app = FastAPI(title="Depot", version="0.0.0")
    app.include_router(health.router)
    app.include_router(products.router)
    return app


app = create_app()
