"""Routes responsible for rendering HTML pages and basic status APIs."""

from fastapi import APIRouter, HTTPException
from fastapi.requests import Request
from fastapi.responses import HTMLResponse, JSONResponse

from ..core import (
    logger,
    auth_manager,
    dataset_repo,
    google_drive,
    paper_repo,
    poster_repo,
    templates,
    user_credentials,
)
from ..services.admin_overview import build_admin_overview

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """メインページ"""
    system_status = {
        "google_drive": google_drive.is_enabled() if google_drive else False,
        "auth": auth_manager.is_enabled(),
        "database": True,
    }

    stats = {
        "papers": len(paper_repo.find_all()),
        "posters": len(poster_repo.find_all()),
        "datasets": len(dataset_repo.find_all()),
    }

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "system_status": system_status,
            "stats": stats,
        },
    )


@router.get("/settings", response_class=HTMLResponse)
async def settings_dashboard(request: Request):
    """設定ダッシュボードページ"""
    overview = build_admin_overview()
    return templates.TemplateResponse(
        "settings.html",
        {
            "request": request,
            "overview": overview,
        },
    )


@router.get("/api/status")
async def get_system_status():
    """システム状態API"""
    return JSONResponse(
        {
            "google_drive": "default" in user_credentials,
            "auth": auth_manager.is_enabled(),
            "database": True,
            "stats": {
                "papers": len(paper_repo.find_all()),
                "posters": len(poster_repo.find_all()),
                "datasets": len(dataset_repo.find_all()),
            },
        }
    )


@router.get("/api/settings/overview")
async def get_settings_overview():
    """設定ダッシュボード向け概要情報API"""
    try:
        overview = build_admin_overview()
        return JSONResponse(overview)
    except Exception as exc:
        logger.error("管理者概要情報APIエラー: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


__all__ = ["router"]
