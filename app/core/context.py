"""Shared application context: singletons, templates, and credential helpers."""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from fastapi.templating import Jinja2Templates
from google.oauth2.credentials import Credentials

from agent.source.advisor.dataset_advisor import DatasetAdvisor
from agent.source.advisor.enhanced_research_advisor import EnhancedResearchAdvisor
from agent.source.analyzer.openrouter_client import OpenRouterClient
from agent.source.database.new_repository import (
    DatasetFileRepository,
    DatasetRepository,
    OpenRouterModelRepository,
    PaperDatasetRelationRepository,
    PaperRepository,
    PosterDatasetRelationRepository,
    PosterRepository,
)
from agent.source.integrations.auth import AuthenticationManager
from agent.source.integrations.looker_export import LookerDataExporter
from agent.source.integrations.openrouter_sync import OpenRouterModelSync
from agent.source.interfaces.vector_service import get_vector_search_service

load_dotenv()

# 開発環境でHTTPを許可（本番環境では削除すること）
os.environ.setdefault("OAUTHLIB_INSECURE_TRANSPORT", "1")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("rnddb.app")

STATIC_DIR = "static"
TEMPLATE_DIR = "templates"

os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(TEMPLATE_DIR, exist_ok=True)

templates = Jinja2Templates(directory=TEMPLATE_DIR)

# グローバルインスタンス
google_drive = None
auth_manager = AuthenticationManager()
enhanced_advisor = EnhancedResearchAdvisor()
dataset_advisor = DatasetAdvisor()
looker_exporter = LookerDataExporter(google_drive) if google_drive else None
llm_client = OpenRouterClient()
model_sync = OpenRouterModelSync()

vector_engine = get_vector_search_service()

dataset_repo = DatasetRepository()
paper_repo = PaperRepository()
poster_repo = PosterRepository()
paper_dataset_rel_repo = PaperDatasetRelationRepository()
poster_dataset_rel_repo = PosterDatasetRelationRepository()
dataset_file_repo = DatasetFileRepository()
model_repo = OpenRouterModelRepository()

# OAuth セッション管理（本番環境ではRedisなどを使用すべき）
oauth_sessions: Dict[str, Dict[str, Any]] = {}
user_credentials: Dict[str, Credentials] = {}

# 認証情報の永続化パス
TOKEN_PATH = "credentials/google_drive_credentials_token.json"


def load_credentials() -> bool:
    """保存されている認証情報を読み込む"""
    logger.info("トークンファイルを読み込み試行: %s", TOKEN_PATH)
    logger.info("ファイル存在確認: %s", os.path.exists(TOKEN_PATH))

    if not os.path.exists(TOKEN_PATH):
        logger.warning("トークンファイルが見つかりません: %s", TOKEN_PATH)
        return False

    try:
        with open(TOKEN_PATH, "r") as file:
            token_data = json.load(file)

        logger.info("トークンデータキー: %s", list(token_data.keys()))

        expiry: Optional[datetime] = None
        if "expiry" in token_data:
            try:
                expiry_str = token_data["expiry"].replace("Z", "")
                if "+" in expiry_str or expiry_str.count("-") > 2:
                    expiry = datetime.fromisoformat(token_data["expiry"].replace("Z", "+00:00")).replace(tzinfo=None)
                else:
                    expiry = datetime.fromisoformat(expiry_str)
                logger.info("トークン有効期限: %s", expiry)
            except Exception as exc:
                logger.warning("有効期限のパースエラー: %s", exc)

        creds = Credentials(
            token=token_data.get("token"),
            refresh_token=token_data.get("refresh_token"),
            token_uri=token_data.get("token_uri"),
            client_id=token_data.get("client_id"),
            client_secret=token_data.get("client_secret"),
            scopes=token_data.get("scopes"),
            expiry=expiry,
        )

        try:
            is_expired = creds.expired if hasattr(creds, "expired") else False
        except TypeError:
            if expiry:
                is_expired = datetime.utcnow() >= expiry
            else:
                is_expired = True

        if is_expired and creds.refresh_token:
            logger.info("トークンが期限切れです。リフレッシュを試行します...")
            try:
                from google.auth.transport.requests import Request

                creds.refresh(Request())
                save_credentials(creds)
                logger.info("トークンリフレッシュ成功")
            except Exception as refresh_error:
                logger.error("トー​​クンリフレッシュ失敗: %s", refresh_error)
                logger.error("新しい認証が必要です。/api/auth/google/loginから認証を行ってください。")
                return False

        user_credentials["default"] = creds
        logger.info("保存された認証情報を読み込みました: %s", TOKEN_PATH)
        logger.info("user_credentialsに格納: keys=%s", list(user_credentials.keys()))
        return True
    except Exception as exc:
        logger.error("認証情報の読み込みエラー: %s", exc)
        import traceback

        logger.error(traceback.format_exc())
        return False


def save_credentials(creds: Credentials) -> None:
    """認証情報をファイルに保存"""
    try:
        os.makedirs(os.path.dirname(TOKEN_PATH), exist_ok=True)
        token_data = {
            "token": creds.token,
            "refresh_token": creds.refresh_token,
            "token_uri": creds.token_uri,
            "client_id": creds.client_id,
            "client_secret": creds.client_secret,
            "scopes": creds.scopes,
        }

        if hasattr(creds, "expiry") and creds.expiry:
            token_data["expiry"] = creds.expiry.isoformat()

        with open(TOKEN_PATH, "w") as file:
            json.dump(token_data, file, indent=2)
        logger.info("認証情報を保存しました: %s", TOKEN_PATH)
    except Exception as exc:
        logger.error("認証情報の保存エラー: %s", exc)
        import traceback

        logger.error(traceback.format_exc())


# 起動時に認証情報を読み込む
load_credentials()


__all__ = [
    "auth_manager",
    "dataset_advisor",
    "dataset_file_repo",
    "dataset_repo",
    "enhanced_advisor",
    "google_drive",
    "load_credentials",
    "logger",
    "llm_client",
    "looker_exporter",
    "model_repo",
    "model_sync",
    "oauth_sessions",
    "paper_dataset_rel_repo",
    "paper_repo",
    "poster_dataset_rel_repo",
    "poster_repo",
    "save_credentials",
    "templates",
    "TOKEN_PATH",
    "user_credentials",
    "vector_engine",
]
