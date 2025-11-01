"""Pydantic schemas for request and response payloads."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class GoogleDriveSyncRequest(BaseModel):
    folder_type: str  # "all", "datasets", "papers", "posters"
    folder_ids: Optional[List[str]] = None  # 複数選択対応
    folder_id: Optional[str] = None  # 既存クライアント互換用


class SearchRequest(BaseModel):
    query: str
    search_type: str = "all"  # "all", "papers", "posters", "datasets"


class ResearchConsultationRequest(BaseModel):
    query: str
    consultation_type: str = "general"  # "general", "database", "planning"
    model: Optional[str] = None  # OpenRouterモデルID（オプション）


class SyncResponse(BaseModel):
    success: bool
    message: str
    files_processed: int
    errors: List[str] = []


class SearchResponse(BaseModel):
    results: List[Dict[str, Any]]
    total: int
    query: str


class ConsultationResponse(BaseModel):
    advice: str
    related_documents: List[Dict[str, Any]] = []
    relevant_datasets: List[Dict[str, Any]] = []
    next_actions: List[str] = []


class LookerExportRequest(BaseModel):
    """Looker Studio用エクスポートリクエスト"""

    export_type: str = "summary"  # Phase 1では"summary"のみ


class LookerExportResponse(BaseModel):
    """Looker Studio用エクスポートレスポンス"""

    success: bool
    message: str
    file_id: Optional[str] = None
    stats: Optional[Dict[str, Any]] = None


class SetFolderRequest(BaseModel):
    folder_ids: Optional[List[str]] = None
    folder_id: Optional[str] = None


__all__ = [
    "ConsultationResponse",
    "GoogleDriveSyncRequest",
    "LookerExportRequest",
    "LookerExportResponse",
    "ResearchConsultationRequest",
    "SearchRequest",
    "SearchResponse",
    "SetFolderRequest",
    "SyncResponse",
]
