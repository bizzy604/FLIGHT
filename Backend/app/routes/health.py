"""Health check endpoints."""

from fastapi import APIRouter
from datetime import datetime, UTC
from app.config import settings

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health_check():
    """
    Health check endpoint.
    
    Returns basic application status and version information.
    """
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "timestamp": datetime.now(UTC).isoformat()
    }


@router.get("/ready")
async def readiness_check():
    """
    Readiness check endpoint.
    
    Indicates if the application is ready to serve traffic.
    """
    return {
        "status": "ready",
        "timestamp": datetime.now(UTC).isoformat()
    }


@router.get("/live")
async def liveness_check():
    """
    Liveness check endpoint.
    
    Indicates if the application is alive and running.
    """
    return {
        "status": "alive",
        "timestamp": datetime.now(UTC).isoformat()
    }
