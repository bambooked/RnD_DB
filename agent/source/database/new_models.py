from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
import json


@dataclass
class Dataset:
    """データセット情報を表すデータクラス"""
    id: Optional[int] = None
    name: str = ""
    description: Optional[str] = None
    file_count: int = 0
    total_size: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    summary: Optional[str] = None

    def to_dict(self) -> dict:
        """辞書形式に変換"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "file_count": self.file_count,
            "total_size": self.total_size,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "summary": self.summary
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Dataset":
        """辞書から作成"""
        if data.get("created_at"):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        if data.get("updated_at"):
            data["updated_at"] = datetime.fromisoformat(data["updated_at"])
        return cls(**data)


@dataclass
class Paper:
    """論文情報を表すデータクラス"""
    id: Optional[int] = None
    file_path: str = ""
    file_name: str = ""
    file_size: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    indexed_at: Optional[datetime] = None
    title: Optional[str] = None
    authors: Optional[str] = None
    abstract: Optional[str] = None
    keywords: Optional[str] = None
    content_hash: Optional[str] = None

    def to_dict(self) -> dict:
        """辞書形式に変換"""
        return {
            "id": self.id,
            "file_path": self.file_path,
            "file_name": self.file_name,
            "file_size": self.file_size,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "indexed_at": self.indexed_at.isoformat() if self.indexed_at else None,
            "title": self.title,
            "authors": self.authors,
            "abstract": self.abstract,
            "keywords": self.keywords,
            "content_hash": self.content_hash
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Paper":
        """辞書から作成"""
        if data.get("created_at"):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        if data.get("updated_at"):
            data["updated_at"] = datetime.fromisoformat(data["updated_at"])
        if data.get("indexed_at"):
            data["indexed_at"] = datetime.fromisoformat(data["indexed_at"])
        return cls(**data)


@dataclass
class Poster:
    """ポスター情報を表すデータクラス"""
    id: Optional[int] = None
    file_path: str = ""
    file_name: str = ""
    file_size: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    indexed_at: Optional[datetime] = None
    title: Optional[str] = None
    authors: Optional[str] = None
    abstract: Optional[str] = None
    keywords: Optional[str] = None
    content_hash: Optional[str] = None

    def to_dict(self) -> dict:
        """辞書形式に変換"""
        return {
            "id": self.id,
            "file_path": self.file_path,
            "file_name": self.file_name,
            "file_size": self.file_size,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "indexed_at": self.indexed_at.isoformat() if self.indexed_at else None,
            "title": self.title,
            "authors": self.authors,
            "abstract": self.abstract,
            "keywords": self.keywords,
            "content_hash": self.content_hash
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Poster":
        """辞書から作成"""
        if data.get("created_at"):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        if data.get("updated_at"):
            data["updated_at"] = datetime.fromisoformat(data["updated_at"])
        if data.get("indexed_at"):
            data["indexed_at"] = datetime.fromisoformat(data["indexed_at"])
        return cls(**data)


@dataclass
class DatasetFile:
    """データセット内ファイル情報を表すデータクラス"""
    id: Optional[int] = None
    dataset_id: int = 0
    file_path: str = ""
    file_name: str = ""
    file_type: str = ""
    file_size: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    indexed_at: Optional[datetime] = None
    content_hash: Optional[str] = None
    schema_info: Optional[str] = None  # JSONスキーマ情報（カラム名、データ型など）
    summary: Optional[str] = None  # ファイルの要約

    def to_dict(self) -> dict:
        """辞書形式に変換"""
        return {
            "id": self.id,
            "dataset_id": self.dataset_id,
            "file_path": self.file_path,
            "file_name": self.file_name,
            "file_type": self.file_type,
            "file_size": self.file_size,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "indexed_at": self.indexed_at.isoformat() if self.indexed_at else None,
            "content_hash": self.content_hash,
            "schema_info": self.schema_info,
            "summary": self.summary
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DatasetFile":
        """辞書から作成"""
        if data.get("created_at"):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        if data.get("updated_at"):
            data["updated_at"] = datetime.fromisoformat(data["updated_at"])
        if data.get("indexed_at"):
            data["indexed_at"] = datetime.fromisoformat(data["indexed_at"])
        return cls(**data)


@dataclass
class PaperDatasetRelation:
    """論文とデータセット間の関連を表すデータクラス"""
    id: Optional[int] = None
    paper_id: int = 0
    dataset_id: int = 0
    relation_type: str = "cited"  # cited, used, created, etc.
    confidence: float = 1.0  # 関連性の信頼度 (0.0-1.0)
    created_at: Optional[datetime] = None
    notes: Optional[str] = None  # 関連性に関する追加情報

    def to_dict(self) -> dict:
        """辞書形式に変換"""
        return {
            "id": self.id,
            "paper_id": self.paper_id,
            "dataset_id": self.dataset_id,
            "relation_type": self.relation_type,
            "confidence": self.confidence,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "notes": self.notes
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PaperDatasetRelation":
        """辞書から作成"""
        if data.get("created_at"):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        return cls(**data)


@dataclass
class PosterDatasetRelation:
    """ポスターとデータセット間の関連を表すデータクラス"""
    id: Optional[int] = None
    poster_id: int = 0
    dataset_id: int = 0
    relation_type: str = "cited"  # cited, used, created, etc.
    confidence: float = 1.0  # 関連性の信頼度 (0.0-1.0)
    created_at: Optional[datetime] = None
    notes: Optional[str] = None  # 関連性に関する追加情報

    def to_dict(self) -> dict:
        """辞書形式に変換"""
        return {
            "id": self.id,
            "poster_id": self.poster_id,
            "dataset_id": self.dataset_id,
            "relation_type": self.relation_type,
            "confidence": self.confidence,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "notes": self.notes
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PosterDatasetRelation":
        """辞書から作成"""
        if data.get("created_at"):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        return cls(**data)