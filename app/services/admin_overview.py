"""Utilities for building administrative overview data."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from services.admin_metrics import admin_metrics

from ..core import (
    auth_manager,
    google_drive,
    logger,
    model_repo,
    model_sync,
    paper_repo,
    poster_repo,
    user_credentials,
    vector_engine,
    vector_indexer,
    dataset_repo,
)


def build_admin_overview(limit: int = 6) -> Dict[str, Any]:
    """管理者ダッシュボード向けの概要情報を生成"""
    try:
        papers = paper_repo.find_all()
        posters = poster_repo.find_all()
        datasets = dataset_repo.find_all()
        paper_count = len(papers)
        poster_count = len(posters)
        dataset_count = len(datasets)
    except Exception as exc:
        logger.error("統計情報取得エラー: %s", exc)
        papers = posters = datasets = []
        paper_count = poster_count = dataset_count = 0

    system_status = {
        "google_drive": google_drive.is_enabled() if google_drive else False,
        "google_drive_connected": "default" in user_credentials,
        "auth": auth_manager.is_enabled(),
        "database": True,
        "vector_search": vector_engine.is_enabled(),
    }

    try:
        vector_status = vector_indexer.get_index_stats()
    except Exception as exc:
        logger.error("ベクトル検索状態取得エラー: %s", exc)
        vector_status = {
            "enabled": False,
            "error": str(exc),
        }

    model_stats: Dict[str, Any] = {
        "total": 0,
        "needs_sync": False,
    }
    try:
        model_stats["total"] = model_repo.count()
        model_stats["needs_sync"] = model_sync.should_update()
    except Exception as exc:
        logger.error("モデル統計情報取得エラー: %s", exc)
        model_stats["error"] = str(exc)

    recent_items: List[Dict[str, Any]] = []

    metrics_snapshot = admin_metrics.get_snapshot()
    llm_usage = metrics_snapshot.get("llm_usage", {}) if isinstance(metrics_snapshot, dict) else {}
    maintenance_events = metrics_snapshot.get("events", []) if isinstance(metrics_snapshot, dict) else []

    def build_timestamped_entry(
        item_type: str,
        title: str,
        detail: Optional[str],
        url: Optional[str],
        dt_obj: Optional[datetime],
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        entry: Dict[str, Any] = {
            "type": item_type,
            "title": title,
            "detail": detail,
            "drive_url": url,
            "_timestamp": dt_obj,
        }
        if extra:
            entry.update(extra)
        recent_items.append(entry)

    try:
        for dataset in datasets[:limit]:
            timestamp = getattr(dataset, "updated_at", None) or getattr(dataset, "created_at", None)
            build_timestamped_entry(
                "dataset",
                getattr(dataset, "name", ""),
                getattr(dataset, "description", None),
                getattr(dataset, "drive_url", None),
                timestamp,
                {
                    "file_count": getattr(dataset, "file_count", None),
                    "total_size": getattr(dataset, "total_size", None),
                },
            )
    except Exception as exc:
        logger.error("データセット履歴取得エラー: %s", exc)

    try:
        for paper in papers[:limit]:
            timestamp = (
                getattr(paper, "updated_at", None)
                or getattr(paper, "indexed_at", None)
                or getattr(paper, "created_at", None)
            )
            build_timestamped_entry(
                "paper",
                getattr(paper, "title", None) or getattr(paper, "file_name", ""),
                getattr(paper, "authors", None),
                getattr(paper, "drive_url", None),
                timestamp,
                {
                    "file_name": getattr(paper, "file_name", None),
                },
            )
    except Exception as exc:
        logger.error("論文履歴取得エラー: %s", exc)

    try:
        for poster in posters[:limit]:
            timestamp = (
                getattr(poster, "updated_at", None)
                or getattr(poster, "indexed_at", None)
                or getattr(poster, "created_at", None)
            )
            build_timestamped_entry(
                "poster",
                getattr(poster, "title", None) or getattr(poster, "file_name", ""),
                getattr(poster, "authors", None),
                getattr(poster, "drive_url", None),
                timestamp,
                {
                    "file_name": getattr(poster, "file_name", None),
                },
            )
    except Exception as exc:
        logger.error("ポスター履歴取得エラー: %s", exc)

    recent_items = [item for item in recent_items if item.get("_timestamp")]
    recent_items.sort(key=lambda x: x.get("_timestamp"), reverse=True)
    recent_items = recent_items[:limit]
    for item in recent_items:
        timestamp = item.pop("_timestamp", None)
        item["timestamp"] = timestamp.isoformat() if timestamp else None

    return {
        "stats": {
            "papers": paper_count,
            "posters": poster_count,
            "datasets": dataset_count,
        },
        "system_status": system_status,
        "vector_status": vector_status,
        "model_stats": model_stats,
        "recent_items": recent_items,
        "llm_usage": llm_usage,
        "maintenance_events": list(reversed(maintenance_events[-limit:])) if maintenance_events else [],
        "generated_at": datetime.now().isoformat(),
    }


__all__ = ["build_admin_overview"]
