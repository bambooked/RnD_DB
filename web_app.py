"""
ASGI entrypoint kept for backward compatibility.
The actual FastAPI application lives in app.main.
"""

from app.main import app

__all__ = ["app"]
