"""
研究データ管理システム Webアプリケーション
Google Drive連携、AI検索・研究相談機能付き
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.requests import Request
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
import asyncio
import logging
from datetime import datetime
import json
import secrets
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# 既存のコンポーネントをインポート
import sys
sys.path.append('.')

from dotenv import load_dotenv
load_dotenv()

# 開発環境でHTTPを許可（本番環境では削除すること）
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

from agent.source.integrations.google_drive import GoogleDriveIntegration
from agent.source.integrations.auth import AuthenticationManager
from agent.source.database.connection import db_connection
from agent.source.database.new_repository import (
    DatasetRepository, PaperRepository, PosterRepository,
    PaperDatasetRelationRepository, PosterDatasetRelationRepository,
    DatasetFileRepository, OpenRouterModelRepository
)
from agent.source.database.new_models import PaperDatasetRelation, PosterDatasetRelation
from agent.source.database.new_models import Dataset, Paper, Poster, DatasetFile
from agent.source.advisor.enhanced_research_advisor import EnhancedResearchAdvisor
from agent.source.advisor.dataset_advisor import DatasetAdvisor
from agent.source.integrations.looker_export import LookerDataExporter
from agent.source.analyzer.openrouter_client import OpenRouterClient
from agent.source.integrations.openrouter_sync import OpenRouterModelSync
from services.admin_metrics import admin_metrics

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPIアプリケーション初期化
app = FastAPI(
    title="研究データ管理システム",
    description="Google Drive連携とAI研究相談機能を備えた研究データ管理システム",
    version="1.0.0"
)

# 静的ファイルとテンプレート設定
os.makedirs("static", exist_ok=True)
os.makedirs("templates", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# グローバルインスタンス
# GoogleDriveIntegrationは新しいOAuthフローを使うため、初期化しない
# google_drive = GoogleDriveIntegration()
google_drive = None
auth_manager = AuthenticationManager()
enhanced_advisor = EnhancedResearchAdvisor()
dataset_advisor = DatasetAdvisor()
looker_exporter = LookerDataExporter(google_drive) if google_drive else None
llm_client = OpenRouterClient()
model_sync = OpenRouterModelSync()

# ベクトル検索関連
from agent.source.integrations.vector_search import VectorSearchEngine
from agent.source.integrations.vector_indexer import VectorIndexer
vector_engine = VectorSearchEngine()
vector_indexer = VectorIndexer()

# リポジトリ
dataset_repo = DatasetRepository()
paper_repo = PaperRepository()
poster_repo = PosterRepository()
paper_dataset_rel_repo = PaperDatasetRelationRepository()
poster_dataset_rel_repo = PosterDatasetRelationRepository()
dataset_file_repo = DatasetFileRepository()
model_repo = OpenRouterModelRepository()

# OAuth セッション管理（本番環境ではRedisなどを使用すべき）
oauth_sessions = {}
user_credentials = {}

# 認証情報の永続化パス
TOKEN_PATH = 'credentials/google_oauth_token.json'

# 起動時に既存のトークンを読み込む
def load_credentials():
    """保存されている認証情報を読み込む"""
    if os.path.exists(TOKEN_PATH):
        try:
            with open(TOKEN_PATH, 'r') as f:
                token_data = json.load(f)
            creds = Credentials(
                token=token_data.get('token'),
                refresh_token=token_data.get('refresh_token'),
                token_uri=token_data.get('token_uri'),
                client_id=token_data.get('client_id'),
                client_secret=token_data.get('client_secret'),
                scopes=token_data.get('scopes')
            )
            user_credentials['default'] = creds
            logger.info("保存された認証情報を読み込みました")
            return True
        except Exception as e:
            logger.error(f"認証情報の読み込みエラー: {e}")
    return False

def save_credentials(creds):
    """認証情報をファイルに保存"""
    try:
        os.makedirs(os.path.dirname(TOKEN_PATH), exist_ok=True)
        token_data = {
            'token': creds.token,
            'refresh_token': creds.refresh_token,
            'token_uri': creds.token_uri,
            'client_id': creds.client_id,
            'client_secret': creds.client_secret,
            'scopes': creds.scopes
        }
        with open(TOKEN_PATH, 'w') as f:
            json.dump(token_data, f)
        logger.info("認証情報を保存しました")
    except Exception as e:
        logger.error(f"認証情報の保存エラー: {e}")

# 起動時に認証情報を読み込む
load_credentials()


def build_admin_overview(limit: int = 6) -> Dict[str, Any]:
    """管理者ダッシュボード向けの概要情報を生成"""
    papers: List[Paper] = []
    posters: List[Poster] = []
    datasets: List[Dataset] = []
    try:
        papers = paper_repo.find_all()
        posters = poster_repo.find_all()
        datasets = dataset_repo.find_all()
        paper_count = len(papers)
        poster_count = len(posters)
        dataset_count = len(datasets)
    except Exception as e:
        logger.error(f"統計情報取得エラー: {e}")
        paper_count = poster_count = dataset_count = 0
        papers = posters = datasets = []

    system_status = {
        "google_drive": google_drive.is_enabled() if google_drive else False,
        "google_drive_connected": 'default' in user_credentials,
        "auth": auth_manager.is_enabled(),
        "database": True,
        "vector_search": vector_engine.is_enabled()
    }

    try:
        vector_status = vector_indexer.get_index_stats()
    except Exception as e:
        logger.error(f"ベクトル検索状態取得エラー: {e}")
        vector_status = {
            "enabled": False,
            "error": str(e)
        }

    model_stats: Dict[str, Any] = {
        "total": 0,
        "needs_sync": False
    }
    try:
        model_stats["total"] = model_repo.count()
        model_stats["needs_sync"] = model_sync.should_update()
    except Exception as e:
        logger.error(f"モデル統計情報取得エラー: {e}")
        model_stats["error"] = str(e)

    recent_items = []

    metrics_snapshot = admin_metrics.get_snapshot()
    llm_usage = metrics_snapshot.get("llm_usage", {}) if isinstance(metrics_snapshot, dict) else {}
    maintenance_events = metrics_snapshot.get("events", []) if isinstance(metrics_snapshot, dict) else []

    def build_timestamped_entry(item_type: str, title: str, detail: Optional[str], url: Optional[str], dt_obj: Optional[datetime], extra: Optional[Dict[str, Any]] = None):
        entry = {
            "type": item_type,
            "title": title,
            "detail": detail,
            "drive_url": url,
            "_timestamp": dt_obj
        }
        if extra:
            entry.update(extra)
        recent_items.append(entry)

    try:
        for dataset in datasets[:limit]:
            timestamp = dataset.updated_at or dataset.created_at
            build_timestamped_entry(
                "dataset",
                dataset.name,
                dataset.description,
                dataset.drive_url,
                timestamp,
                {
                    "file_count": dataset.file_count,
                    "total_size": dataset.total_size
                }
            )
    except Exception as e:
        logger.error(f"データセット履歴取得エラー: {e}")

    try:
        for paper in papers[:limit]:
            timestamp = paper.updated_at or paper.indexed_at or paper.created_at
            build_timestamped_entry(
                "paper",
                paper.title or paper.file_name,
                paper.authors,
                paper.drive_url,
                timestamp,
                {
                    "file_name": paper.file_name
                }
            )
    except Exception as e:
        logger.error(f"論文履歴取得エラー: {e}")

    try:
        for poster in posters[:limit]:
            timestamp = poster.updated_at or poster.indexed_at or poster.created_at
            build_timestamped_entry(
                "poster",
                poster.title or poster.file_name,
                poster.authors,
                poster.drive_url,
                timestamp,
                {
                    "file_name": poster.file_name
                }
            )
    except Exception as e:
        logger.error(f"ポスター履歴取得エラー: {e}")

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
            "datasets": dataset_count
        },
        "system_status": system_status,
        "vector_status": vector_status,
        "model_stats": model_stats,
        "recent_items": recent_items,
        "llm_usage": llm_usage,
        "maintenance_events": list(reversed(maintenance_events[-limit:])) if maintenance_events else [],
        "generated_at": datetime.now().isoformat()
    }

# バックグラウンドタスク管理
import threading
import time

def background_model_sync_task():
    """24時間ごとにOpenRouterモデル一覧を同期するバックグラウンドタスク"""
    while True:
        try:
            logger.info("バックグラウンドタスク: OpenRouterモデル一覧の同期を開始")
            result = model_sync.sync_if_needed()
            if result.get("success"):
                logger.info(f"バックグラウンドタスク: {result.get('message')}")
            else:
                logger.error(f"バックグラウンドタスク: {result.get('message')}")
        except Exception as e:
            logger.error(f"バックグラウンドタスクエラー: {e}")

        # 24時間待機
        time.sleep(24 * 60 * 60)

# バックグラウンドタスクを起動
background_thread = None

# リクエスト/レスポンスモデル
class GoogleDriveSyncRequest(BaseModel):
    folder_type: str  # "all", "datasets", "papers", "posters"
    folder_id: str  # Google Drive folder ID to sync

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

# データベース初期化
@app.on_event("startup")
async def startup_event():
    """アプリケーション起動時の初期化"""
    global background_thread

    logger.info("研究データ管理システム Webアプリ起動中...")

    # データベース初期化
    db_connection.initialize_database()
    logger.info("データベース初期化完了")

    # OpenRouterモデル一覧の初回同期
    try:
        logger.info("OpenRouterモデル一覧の初回同期を実行...")
        result = model_sync.sync_if_needed()
        if result.get("success"):
            logger.info(f"モデル同期完了: {result.get('message')}")
        else:
            logger.warning(f"モデル同期スキップまたは失敗: {result.get('message')}")
    except Exception as e:
        logger.error(f"モデル同期エラー: {e}")

    # バックグラウンドタスクを起動
    if background_thread is None or not background_thread.is_alive():
        background_thread = threading.Thread(
            target=background_model_sync_task,
            daemon=True,
            name="OpenRouterModelSync"
        )
        background_thread.start()
        logger.info("バックグラウンドタスク（モデル同期）を起動しました")

    # 統合機能確認
    integrations = []
    if google_drive and google_drive.is_enabled():
        integrations.append("Google Drive")
    if auth_manager.is_enabled():
        integrations.append("認証システム")

    if integrations:
        logger.info(f"統合機能が有効: {', '.join(integrations)}")

    logger.info("研究データ管理システム Webアプリ起動完了")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """メインページ"""
    # システム状態確認
    system_status = {
        "google_drive": google_drive.is_enabled() if google_drive else False,
        "auth": auth_manager.is_enabled(),
        "database": True
    }

    # 統計情報取得
    stats = {
        "papers": len(paper_repo.find_all()),
        "posters": len(poster_repo.find_all()),
        "datasets": len(dataset_repo.find_all())
    }

    return templates.TemplateResponse("index.html", {
        "request": request,
        "system_status": system_status,
        "stats": stats
    })


@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    """管理者ダッシュボードページ"""
    overview = build_admin_overview()
    return templates.TemplateResponse("admin.html", {
        "request": request,
        "overview": overview
    })

@app.get("/api/status")
async def get_system_status():
    """システム状態API"""
    return JSONResponse({
        "google_drive": 'default' in user_credentials,
        "auth": auth_manager.is_enabled(),
        "database": True,
        "stats": {
            "papers": len(paper_repo.find_all()),
            "posters": len(poster_repo.find_all()),
            "datasets": len(dataset_repo.find_all())
        }
    })


@app.get("/api/admin/overview")
async def get_admin_overview():
    """管理者ダッシュボード向け概要情報API"""
    try:
        overview = build_admin_overview()
        return JSONResponse(overview)
    except Exception as e:
        logger.error(f"管理者概要情報APIエラー: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/sync/google-drive", response_model=SyncResponse)
async def sync_google_drive(request: GoogleDriveSyncRequest, background_tasks: BackgroundTasks):
    """Google Drive同期API"""
    if 'default' not in user_credentials:
        raise HTTPException(status_code=401, detail="Google認証が必要です")

    try:
        # バックグラウンドで同期実行
        background_tasks.add_task(perform_google_drive_sync, request.folder_type, request.folder_id)

        return SyncResponse(
            success=True,
            message="Google Drive同期を開始しました",
            files_processed=0
        )
    except Exception as e:
        logger.error(f"Google Drive同期エラー: {e}")
        raise HTTPException(status_code=500, detail=f"同期エラー: {str(e)}")

async def perform_google_drive_sync(folder_type: str, folder_id: str):
    """Google Drive同期の実際の処理"""
    try:
        logger.info(f"Google Drive同期開始: {folder_type}, folder_id: {folder_id}")
        source_folder_id = folder_id

        if 'default' not in user_credentials:
            logger.error("認証情報がありません")
            return

        # Google Drive APIサービスを作成
        creds = user_credentials['default']
        service = build('drive', 'v3', credentials=creds)

        # フォルダIDが渡されていない場合は環境変数から取得
        if not folder_id:
            folder_id = os.getenv('GOOGLE_DRIVE_FOLDER_ID')
            if not folder_id:
                logger.error("GOOGLE_DRIVE_FOLDER_IDが設定されていません")
                return

        results = service.files().list(
            q=f"'{folder_id}' in parents and trashed=false",
            pageSize=100,
            fields="files(id, name, mimeType, parents)"
        ).execute()

        folders = results.get('files', [])
        files_processed = 0
        errors = []

        # フェーズ1: データセットを先に処理（cited_datasetsの参照先を作成）
        logger.info("Phase 1: データセットの処理開始")

        # folder_type が "all" または "datasets" の場合、全てのフォルダをデータセットとして処理
        if folder_type in ["all", "datasets"]:
            logger.info(f"データセットフォルダを処理: {len(folders)}個のサブフォルダ")
            dataset_files_count = await process_datasets_folder(folders, service)
            files_processed += dataset_files_count
        else:
            # 従来の処理（個別フォルダ指定の場合）
            for folder in folders:
                if folder.get('mimeType') == 'application/vnd.google-apps.folder':
                    folder_name = folder['name']
                    folder_id_sub = folder['id']

                    # フォルダタイプでフィルタ
                    if folder_name not in [folder_type, f"{folder_type}s"]:
                        continue

                    if folder_name == 'datasets':
                        # フォルダ内のファイルを処理
                        results = service.files().list(
                            q=f"'{folder_id_sub}' in parents and trashed=false",
                            pageSize=100,
                            fields="files(id, name, mimeType, parents)"
                        ).execute()
                        files_in_folder = results.get('files', [])
                        # datasetsフォルダの場合、サブフォルダを処理
                        dataset_files_count = await process_datasets_folder(files_in_folder, service)
                        files_processed += dataset_files_count

        # フェーズ2: 論文・ポスターを処理（cited_datasetsの関連を作成）
        logger.info("Phase 2: 論文・ポスターの処理開始")
        for folder in folders:
            if folder.get('mimeType') == 'application/vnd.google-apps.folder':
                folder_name = folder['name']
                folder_id = folder['id']

                # フォルダタイプでフィルタ
                if folder_type != "all" and folder_name not in [folder_type, f"{folder_type}s"]:
                    continue

                # フォルダ内のファイルを処理
                results = service.files().list(
                    q=f"'{folder_id}' in parents and trashed=false",
                    pageSize=100,
                    fields="files(id, name, mimeType, parents)"
                ).execute()
                files_in_folder = results.get('files', [])

                if folder_name != 'datasets':
                    # 通常のフォルダ（paper, poster）の場合
                    for file in files_in_folder:
                        if file.get('mimeType') != 'application/vnd.google-apps.folder':
                            try:
                                await process_drive_file(file, folder_name, service)
                                files_processed += 1
                            except Exception as e:
                                errors.append(f"{file['name']}: {str(e)}")
        
        logger.info(f"Google Drive同期完了: {files_processed}ファイル処理, {len(errors)}エラー")

        # 統計情報を更新（キャッシュクリア効果）
        stats = {
            "papers": len(paper_repo.find_all()),
            "posters": len(poster_repo.find_all()),
            "datasets": len(dataset_repo.find_all())
        }
        logger.info(f"同期後統計: 論文{stats['papers']}件, ポスター{stats['posters']}件, データセット{stats['datasets']}件")

        admin_metrics.record_event(
            "drive_sync",
            "success" if not errors else "partial",
            f"Google Drive同期完了: {files_processed}件処理 (エラー{len(errors)}件)",
            extra={
                "folder_type": folder_type,
                "folder_id": source_folder_id,
                "files_processed": files_processed,
                "error_count": len(errors),
                "errors": errors[:10]
            }
        )

    except Exception as e:
        logger.error(f"Google Drive同期エラー: {e}")
        admin_metrics.record_event(
            "drive_sync",
            "error",
            f"Google Drive同期失敗: {str(e)}",
            extra={
                "folder_type": folder_type,
                "folder_id": source_folder_id if 'source_folder_id' in locals() else folder_id
            }
        )

async def process_datasets_folder(dataset_items: List[Dict[str, Any]], service) -> int:
    """datasetsフォルダ内のサブフォルダを処理"""
    files_processed = 0

    for item in dataset_items:
        if item.get('mimeType') == 'application/vnd.google-apps.folder':
            # データセットサブフォルダ
            dataset_name = item['name']
            dataset_folder_id = item['id']

            logger.info(f"データセット処理開始: {dataset_name}")

            # データセットフォルダ内のファイルを取得
            results = service.files().list(
                q=f"'{dataset_folder_id}' in parents and trashed=false",
                pageSize=100,
                fields="files(id, name, mimeType, size, createdTime, modifiedTime)"
            ).execute()
            dataset_files = results.get('files', [])
            
            # 既存データセット確認
            existing_dataset = dataset_repo.find_by_name(dataset_name)
            
            dataset_file_list = []
            total_size = 0
            
            # ファイルを処理
            for file in dataset_files:
                if file.get('mimeType') != 'application/vnd.google-apps.folder':
                    file_info = {
                        'name': file['name'],
                        'id': file['id'],
                        'size': int(file.get('size', 0)),
                        'created_time': file.get('createdTime', ''),
                        'modified_time': file.get('modifiedTime', ''),
                        'mime_type': file.get('mimeType', '')
                    }
                    dataset_file_list.append(file_info)
                    total_size += file_info['size']
                    files_processed += 1

                    # CSV/JSONファイルの場合は解析を実行
                    extension = file_info['name'].split('.')[-1].lower() if '.' in file_info['name'] else ''
                    if extension in ['csv', 'json', 'jsonl']:
                        logger.info(f"データセットファイル解析開始: {file_info['name']}")
                        file_analysis = await analyze_dataset_file(file_info['id'], file_info['name'], extension, service)

                        # DatasetFileレコードを作成または更新
                        if existing_dataset:
                            file_path = f"gdrive://dataset/{dataset_name}/{file_info['id']}"
                            existing_file = dataset_file_repo.find_by_path(file_path)

                            if existing_file:
                                # 既存ファイルの更新
                                if file_analysis['schema_info']:
                                    # スキーマ情報を更新（完全置換ではなくマージする場合はロジックを変更）
                                    existing_file.schema_info = file_analysis['schema_info']
                                    existing_file.summary = file_analysis['summary']
                                    dataset_file_repo.update(existing_file)
                                    logger.info(f"データセットファイル情報更新: {file_info['name']}")
                            else:
                                # Google Drive URL を生成
                                drive_url = f"https://drive.google.com/file/d/{file_info['id']}/view"

                                # 新規ファイル登録
                                dataset_file = DatasetFile(
                                    dataset_id=existing_dataset.id,
                                    file_path=file_path,
                                    file_name=file_info['name'],
                                    file_type=extension,
                                    file_size=file_info['size'],
                                    schema_info=file_analysis['schema_info'],
                                    summary=file_analysis['summary'],
                                    drive_file_id=file_info['id'],
                                    drive_url=drive_url
                                )
                                dataset_file_repo.create(dataset_file)
                                logger.info(f"データセットファイル登録: {file_info['name']}")
            
            if dataset_file_list:
                # データセット解説を生成
                dataset_description = None
                if len(dataset_file_list) > 0:
                    logger.info(f"データセット解説生成開始: {dataset_name}")
                    dataset_description = llm_client.generate_dataset_description(
                        dataset_name,
                        [{'name': f['name'], 'type': f['mime_type'], 'size': f['size']} for f in dataset_file_list]
                    )

                # データセットフォルダのGoogle Drive URL
                dataset_folder_url = f"https://drive.google.com/drive/folders/{dataset_folder_id}"

                if existing_dataset:
                    # 既存データセットの更新
                    needs_update = False

                    # ファイル数やサイズが変わった場合
                    if existing_dataset.file_count != len(dataset_file_list) or existing_dataset.total_size != total_size:
                        existing_dataset.file_count = len(dataset_file_list)
                        existing_dataset.total_size = total_size
                        needs_update = True

                    # 解説が無い場合は追加
                    if dataset_description and not existing_dataset.summary:
                        existing_dataset.summary = dataset_description
                        needs_update = True
                        logger.info(f"データセット解説を追加: {dataset_name}")

                    # drive_url が無い場合は追加
                    logger.info(f"データセット {dataset_name} の drive_folder_id 確認: {existing_dataset.drive_folder_id}")
                    if not existing_dataset.drive_folder_id:
                        logger.info(f"drive_url を設定: {dataset_folder_url}")
                        existing_dataset.drive_folder_id = dataset_folder_id
                        existing_dataset.drive_url = dataset_folder_url
                        needs_update = True
                    else:
                        logger.info(f"drive_folder_id 既に存在: {existing_dataset.drive_folder_id}")

                    if needs_update:
                        dataset_repo.update(existing_dataset)
                        logger.info(f"データセット更新: {dataset_name} ({len(dataset_file_list)}ファイル)")
                else:
                    # 新規データセット作成
                    new_dataset = Dataset(
                        name=dataset_name,
                        description=f"Google Driveから同期: {len(dataset_file_list)}ファイル",
                        file_count=len(dataset_file_list),
                        total_size=total_size,
                        summary=dataset_description if dataset_description else None,
                        drive_folder_id=dataset_folder_id,
                        drive_url=dataset_folder_url
                    )
                    dataset_repo.create(new_dataset)
                    logger.info(f"データセット新規作成: {dataset_name} ({len(dataset_file_list)}ファイル)")
    
    return files_processed

async def analyze_dataset_file(file_id: str, file_name: str, file_type: str, service) -> Dict[str, Any]:
    """データセットファイル（CSV/JSON）をダウンロードして解析"""
    try:
        import tempfile
        import pandas as pd
        import json
        from googleapiclient.http import MediaIoBaseDownload
        import io

        # ファイル拡張子からタイプを判定
        extension = file_name.split('.')[-1].lower() if '.' in file_name else ''

        # 一時ファイルを作成
        with tempfile.NamedTemporaryFile(suffix=f'.{extension}', delete=False) as tmp_file:
            tmp_path = tmp_file.name

        # Google Driveからファイルをダウンロード
        request = service.files().get_media(fileId=file_id)
        fh = io.FileIO(tmp_path, 'wb')
        downloader = MediaIoBaseDownload(fh, request)

        done = False
        while not done:
            status, done = downloader.next_chunk()
        fh.close()

        try:
            schema_info = {}
            summary = ''

            if extension == 'csv':
                # CSVファイルの解析
                df = pd.read_csv(tmp_path, nrows=100)  # 最初の100行のみ読み込み
                schema_info = {
                    'columns': list(df.columns),
                    'dtypes': {col: str(dtype) for col, dtype in df.dtypes.items()},
                    'row_count_sample': len(df),
                    'null_counts': df.isnull().sum().to_dict()
                }

                # LLMでサマリーを生成（必要に応じて利用）
                content_preview = f"Columns: {', '.join(df.columns)}\n\nFirst 10 rows:\n{df.head(10).to_string()}"

                # 簡易的な要約（LLMなしで生成）
                summary = f"CSV file with {len(df.columns)} columns: {', '.join(list(df.columns)[:5])}"
                if len(df.columns) > 5:
                    summary += f" and {len(df.columns) - 5} more"

            elif extension in ['json', 'jsonl']:
                # JSONファイルの解析
                if extension == 'jsonl':
                    with open(tmp_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()[:100]
                        sample_data = [json.loads(line) for line in lines[:5]]
                        schema_info = {
                            'format': 'jsonl',
                            'line_count_sample': len(lines),
                            'sample_keys': list(sample_data[0].keys()) if sample_data else []
                        }
                        content_preview = json.dumps(sample_data, indent=2, ensure_ascii=False)
                else:
                    with open(tmp_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            schema_info = {
                                'format': 'json_array',
                                'array_length': len(data),
                                'sample_keys': list(data[0].keys()) if data and isinstance(data[0], dict) else []
                            }
                        else:
                            schema_info = {
                                'format': 'json_object',
                                'keys': list(data.keys()) if isinstance(data, dict) else []
                            }
                        content_preview = json.dumps(data, indent=2, ensure_ascii=False)[:5000]

                # 簡易的な要約（LLMなしで生成）
                if schema_info.get('format') == 'jsonl':
                    summary = f"JSONL file with {schema_info.get('line_count_sample', 0)} lines"
                    if schema_info.get('sample_keys'):
                        summary += f", keys: {', '.join(schema_info['sample_keys'][:3])}"
                elif schema_info.get('format') == 'json_array':
                    summary = f"JSON array with {schema_info.get('array_length', 0)} items"
                    if schema_info.get('sample_keys'):
                        summary += f", keys: {', '.join(schema_info['sample_keys'][:3])}"
                else:
                    summary = f"JSON object with keys: {', '.join(schema_info.get('keys', [])[:5])}"

            return {
                'schema_info': json.dumps(schema_info, ensure_ascii=False),
                'summary': summary
            }

        except Exception as e:
            logger.error(f"ファイル解析エラー: {file_name}, {e}")
            return {'schema_info': None, 'summary': ''}
        finally:
            # 一時ファイルを削除
            try:
                os.remove(tmp_path)
            except:
                pass

    except Exception as e:
        logger.error(f"データセットファイル処理エラー: {file_name}, {e}")
        return {'schema_info': None, 'summary': ''}


def save_cited_datasets(item_id: int, cited_datasets: List[str], item_type: str = 'paper'):
    """引用データセットをDBに保存"""
    try:
        if not cited_datasets:
            return

        for dataset_name in cited_datasets:
            dataset_name_clean = dataset_name.strip()

            # データセットをデータベースから検索（完全一致）
            dataset = dataset_repo.find_by_name(dataset_name_clean)

            # 完全一致が見つからない場合、部分一致・大文字小文字無視で検索
            if not dataset:
                all_datasets = dataset_repo.find_all()
                dataset_name_lower = dataset_name_clean.lower()

                # 部分一致検索
                for ds in all_datasets:
                    if dataset_name_lower in ds.name.lower() or ds.name.lower() in dataset_name_lower:
                        dataset = ds
                        logger.info(f"部分一致でデータセット発見: '{dataset_name_clean}' -> '{ds.name}'")
                        break

            if dataset:
                # 既存の関連を確認
                if item_type == 'paper':
                    existing = paper_dataset_rel_repo.find_by_both_ids(item_id, dataset.id)
                    if not existing:
                        relation = PaperDatasetRelation(
                            paper_id=item_id,
                            dataset_id=dataset.id,
                            relation_type='cited',
                            confidence=0.8,  # LLMからの抽出なので少し低めの信頼度
                            notes='Extracted from PDF content by LLM (OpenRouter)'
                        )
                        paper_dataset_rel_repo.create(relation)
                        logger.info(f"論文-データセット関連を保存: Paper#{item_id} -> {dataset_name}")
                else:  # poster
                    existing = poster_dataset_rel_repo.find_by_both_ids(item_id, dataset.id)
                    if not existing:
                        relation = PosterDatasetRelation(
                            poster_id=item_id,
                            dataset_id=dataset.id,
                            relation_type='cited',
                            confidence=0.8,
                            notes='Extracted from PDF content by LLM (OpenRouter)'
                        )
                        poster_dataset_rel_repo.create(relation)
                        logger.info(f"ポスター-データセット関連を保存: Poster#{item_id} -> {dataset_name}")
            else:
                logger.warning(f"引用データセットがDB内に見つかりません: {dataset_name}")

    except Exception as e:
        logger.error(f"cited_datasets保存エラー: {e}")


async def analyze_pdf_content(file_id: str, file_name: str, service) -> Dict[str, Any]:
    """PDFファイルをダウンロードして内容を解析"""
    try:
        import tempfile
        from pypdf import PdfReader
        from googleapiclient.http import MediaIoBaseDownload
        import io

        # 一時ファイルを作成
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            tmp_path = tmp_file.name

        # Google DriveからPDFをダウンロード
        request = service.files().get_media(fileId=file_id)
        fh = io.FileIO(tmp_path, 'wb')
        downloader = MediaIoBaseDownload(fh, request)

        done = False
        while not done:
            status, done = downloader.next_chunk()
        fh.close()

        # PDFからテキストを抽出
        try:
            text_content = []
            with open(tmp_path, 'rb') as pdf_file:
                pdf_reader = PdfReader(pdf_file)
                # 最初の5ページのみ抽出（要約用）
                for page_num in range(min(5, len(pdf_reader.pages))):
                    try:
                        text = pdf_reader.pages[page_num].extract_text()
                        if text:
                            text_content.append(text)
                    except:
                        pass

            full_text = "\n\n".join(text_content)

            # LLMで解析
            if full_text.strip():
                analysis = llm_client.analyze_paper_metadata(file_name, full_text[:10000])  # 最初の10000文字
                if analysis and isinstance(analysis, dict):
                    logger.info(f"PDF解析完了: {file_name}")
                    # 必須フィールドの確認と補完
                    analysis.setdefault('title', file_name.replace('.pdf', ''))
                    analysis.setdefault('authors', '')
                    analysis.setdefault('abstract', '')
                    analysis.setdefault('keywords', '')
                    analysis.setdefault('cited_datasets', [])
                    return analysis
                else:
                    logger.warning(f"PDF解析結果が不正: {file_name}")

        except Exception as e:
            logger.error(f"PDF解析エラー: {file_name}, {e}")
        finally:
            # 一時ファイルを削除
            try:
                os.remove(tmp_path)
            except:
                pass

        # 解析失敗時のデフォルト
        return {
            'title': file_name.replace('.pdf', ''),
            'authors': '',
            'abstract': '',
            'keywords': '',
            'cited_datasets': []
        }

    except Exception as e:
        logger.error(f"PDF処理エラー: {file_name}, {e}")
        return {
            'title': file_name.replace('.pdf', ''),
            'authors': '',
            'abstract': '',
            'keywords': '',
            'cited_datasets': []
        }

async def process_drive_file(file: Dict[str, Any], folder_name: str, service):
    """個別ファイルの処理"""
    file_info = {
        'name': file['name'],
        'id': file['id'],
        'size': file.get('size', 0),
        'created_time': file.get('createdTime', ''),
        'modified_time': file.get('modifiedTime', ''),
        'mime_type': file.get('mimeType', '')
    }

    try:
        if folder_name == 'paper':
            # Google Drive IDをfile_pathとして使用
            drive_file_path = f"gdrive://paper/{file_info['id']}"

            # 既存確認（file_pathで重複チェック）
            existing_papers = paper_repo.find_all()
            existing_paper = next((p for p in existing_papers if p.file_path == drive_file_path), None)

            # 既存データがあり、内容が揃っている場合はスキップ
            if existing_paper and existing_paper.title and existing_paper.abstract:
                logger.info(f"論文スキップ（既存）: {file_info['name']}")
                return

            # ファイル名での重複チェック（フォールバック）
            if any(p.file_name == file_info["name"] for p in existing_papers):
                logger.info(f"論文スキップ（同名ファイル）: {file_info['name']}")
                return

            # PDFファイルの場合は内容を解析
            metadata = {'title': file_info["name"].replace('.pdf', ''), 'authors': '', 'abstract': '', 'keywords': '', 'cited_datasets': []}
            if file_info['name'].lower().endswith('.pdf'):
                logger.info(f"PDF解析開始: {file_info['name']}")
                metadata = await analyze_pdf_content(file_info['id'], file_info['name'], service)

            if existing_paper:
                # 既存の論文を更新（内容が不完全な場合のみ）
                existing_paper.title = metadata.get('title', existing_paper.title)
                existing_paper.authors = metadata.get('authors', existing_paper.authors)
                existing_paper.abstract = metadata.get('abstract', existing_paper.abstract)
                existing_paper.keywords = metadata.get('keywords', existing_paper.keywords)
                paper_repo.update(existing_paper)

                # cited_datasetsを保存
                cited_datasets = metadata.get('cited_datasets', [])
                if cited_datasets:
                    save_cited_datasets(existing_paper.id, cited_datasets, 'paper')

                logger.info(f"論文情報更新: {file_info['name']}")
                return

            # Google Drive URL を生成
            drive_url = f"https://drive.google.com/file/d/{file_info['id']}/view"

            # 論文として登録
            paper = Paper(
                file_path=drive_file_path,
                file_name=file_info["name"],
                title=metadata.get('title', file_info["name"].replace('.pdf', '')),
                authors=metadata.get('authors', ''),
                abstract=metadata.get('abstract', ''),
                keywords=metadata.get('keywords', ''),
                file_size=int(file_info.get('size', 0)),
                drive_file_id=file_info['id'],
                drive_url=drive_url
            )
            paper_repo.create(paper)

            # cited_datasetsを保存
            cited_datasets = metadata.get('cited_datasets', [])
            if cited_datasets:
                save_cited_datasets(paper.id, cited_datasets, 'paper')

            logger.info(f"論文登録完了: {file_info['name']}")
            
        elif folder_name == 'poster':
            # Google Drive IDをfile_pathとして使用
            drive_file_path = f"gdrive://poster/{file_info['id']}"

            # 既存確認（file_pathで重複チェック）
            existing_posters = poster_repo.find_all()
            existing_poster = next((p for p in existing_posters if p.file_path == drive_file_path), None)

            # 既存データがあり、内容が揃っている場合はスキップ
            if existing_poster and existing_poster.title and existing_poster.abstract:
                logger.info(f"ポスタースキップ（既存）: {file_info['name']}")
                return

            # ファイル名での重複チェック（フォールバック）
            if any(p.file_name == file_info["name"] for p in existing_posters):
                logger.info(f"ポスタースキップ（同名ファイル）: {file_info['name']}")
                return

            # PDFファイルの場合は内容を解析
            metadata = {'title': file_info["name"].replace('.pdf', ''), 'authors': '', 'abstract': '', 'keywords': '', 'cited_datasets': []}
            if file_info['name'].lower().endswith('.pdf'):
                logger.info(f"ポスターPDF解析開始: {file_info['name']}")
                metadata = await analyze_pdf_content(file_info['id'], file_info['name'], service)

            if existing_poster:
                # 既存のポスターを更新（内容が不完全な場合のみ）
                existing_poster.title = metadata.get('title', existing_poster.title)
                existing_poster.authors = metadata.get('authors', existing_poster.authors)
                existing_poster.abstract = metadata.get('abstract', existing_poster.abstract)
                existing_poster.keywords = metadata.get('keywords', existing_poster.keywords)
                poster_repo.update(existing_poster)

                # cited_datasetsを保存
                cited_datasets = metadata.get('cited_datasets', [])
                if cited_datasets:
                    save_cited_datasets(existing_poster.id, cited_datasets, 'poster')

                logger.info(f"ポスター情報更新: {file_info['name']}")
                return

            # Google Drive URL を生成
            drive_url = f"https://drive.google.com/file/d/{file_info['id']}/view"

            # ポスターとして登録
            poster = Poster(
                file_path=drive_file_path,
                file_name=file_info["name"],
                title=metadata.get('title', file_info["name"].replace('.pdf', '')),
                authors=metadata.get('authors', ''),
                abstract=metadata.get('abstract', ''),
                keywords=metadata.get('keywords', ''),
                file_size=int(file_info.get('size', 0)),
                drive_file_id=file_info['id'],
                drive_url=drive_url
            )
            poster_repo.create(poster)

            # cited_datasetsを保存
            cited_datasets = metadata.get('cited_datasets', [])
            if cited_datasets:
                save_cited_datasets(poster.id, cited_datasets, 'poster')

            logger.info(f"ポスター登録完了: {file_info['name']}")
            
        elif folder_name == 'datasets':
            # datasetsフォルダの場合、これはサブフォルダなので処理をスキップ
            # サブフォルダの処理は perform_google_drive_sync で行う
            logger.info(f"データセットサブフォルダをスキップ: {file_info['name']}")
            return
            
    except Exception as e:
        if "UNIQUE constraint failed" in str(e):
            logger.info(f"ファイル重複スキップ: {file_info['name']}")
        else:
            logger.error(f"ファイル処理エラー: {file_info['name']} - {e}")
            raise e  # 重複エラー以外は再発生

@app.post("/api/search", response_model=SearchResponse)
async def search_research_data(request: SearchRequest):
    """研究データ検索API"""
    try:
        results = []
        
        if request.search_type in ["all", "papers"]:
            papers = paper_repo.find_all()
            for paper in papers:
                if request.query.lower() in paper.file_name.lower() or \
                   (paper.title and request.query.lower() in paper.title.lower()):
                    results.append({
                        "type": "paper",
                        "id": paper.id,
                        "title": paper.title or paper.file_name,
                        "file_name": paper.file_name,
                        "authors": paper.authors,
                        "abstract": paper.abstract,
                        "file_size": paper.file_size,
                        "drive_url": paper.drive_url
                    })
        
        if request.search_type in ["all", "posters"]:
            posters = poster_repo.find_all()
            for poster in posters:
                if request.query.lower() in poster.file_name.lower() or \
                   (poster.title and request.query.lower() in poster.title.lower()):
                    results.append({
                        "type": "poster",
                        "id": poster.id,
                        "title": poster.title or poster.file_name,
                        "file_name": poster.file_name,
                        "authors": poster.authors,
                        "abstract": poster.abstract,
                        "file_size": poster.file_size,
                        "drive_url": poster.drive_url
                    })
        
        if request.search_type in ["all", "datasets"]:
            datasets = dataset_repo.find_all()
            for dataset in datasets:
                if request.query.lower() in dataset.name.lower():
                    results.append({
                        "type": "dataset",
                        "id": dataset.id,
                        "name": dataset.name,
                        "description": dataset.description,
                        "file_count": dataset.file_count,
                        "total_size": dataset.total_size,
                        "drive_url": dataset.drive_url
                    })
        
        return SearchResponse(
            results=results,
            total=len(results),
            query=request.query
        )
        
    except Exception as e:
        logger.error(f"検索エラー: {e}")
        raise HTTPException(status_code=500, detail=f"検索エラー: {str(e)}")

@app.post("/api/consultation", response_model=ConsultationResponse)
async def research_consultation(request: ResearchConsultationRequest):
    """AI研究相談API"""
    try:
        # 相談タイプとモデル指定を渡して適切な処理を実行
        result = enhanced_advisor.research_consultation(
            request.query,
            consultation_type=request.consultation_type,
            model=request.model
        )

        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])

        return ConsultationResponse(
            advice=result.get("advice", ""),
            related_documents=result.get("related_documents", []),
            relevant_datasets=result.get("relevant_datasets", []),
            next_actions=result.get("next_actions", [])
        )

    except Exception as e:
        logger.error(f"研究相談エラー: {e}")
        raise HTTPException(status_code=500, detail=f"研究相談エラー: {str(e)}")

@app.get("/api/database/summary")
async def get_database_summary():
    """データベースの詳細な要約情報を取得"""
    try:
        # 論文情報（引用データセット含む）
        papers = paper_repo.find_all()
        papers_summary = []
        for p in papers:
            # 引用データセット情報を取得
            cited_datasets = []
            rels = paper_dataset_rel_repo.find_by_paper_id(p.id)
            for rel in rels:
                ds = dataset_repo.find_by_id(rel.dataset_id)
                if ds:
                    cited_datasets.append({
                        "id": ds.id,
                        "name": ds.name,
                        "confidence": rel.confidence
                    })

            papers_summary.append({
                "id": p.id,
                "file_name": p.file_name,
                "title": p.title,
                "authors": p.authors,
                "abstract": p.abstract[:200] + "..." if p.abstract and len(p.abstract) > 200 else p.abstract,
                "keywords": p.keywords,
                "file_size": p.file_size,
                "cited_datasets": cited_datasets,
                "drive_url": p.drive_url
            })

        # ポスター情報（引用データセット含む）
        posters = poster_repo.find_all()
        posters_summary = []
        for p in posters:
            # 引用データセット情報を取得
            cited_datasets = []
            rels = poster_dataset_rel_repo.find_by_poster_id(p.id)
            for rel in rels:
                ds = dataset_repo.find_by_id(rel.dataset_id)
                if ds:
                    cited_datasets.append({
                        "id": ds.id,
                        "name": ds.name,
                        "confidence": rel.confidence
                    })

            posters_summary.append({
                "id": p.id,
                "file_name": p.file_name,
                "title": p.title,
                "authors": p.authors,
                "abstract": p.abstract[:200] + "..." if p.abstract and len(p.abstract) > 200 else p.abstract,
                "keywords": p.keywords,
                "file_size": p.file_size,
                "cited_datasets": cited_datasets,
                "drive_url": p.drive_url
            })

        # データセット情報（引用元の論文・ポスター含む）
        datasets = dataset_repo.find_all()
        datasets_summary = []
        for d in datasets:
            # このデータセットを引用している論文・ポスターを取得
            citing_papers = []
            paper_rels = paper_dataset_rel_repo.find_by_dataset_id(d.id)
            for rel in paper_rels:
                paper = paper_repo.find_by_id(rel.paper_id)
                if paper:
                    citing_papers.append({
                        "id": paper.id,
                        "title": paper.title,
                        "authors": paper.authors
                    })

            citing_posters = []
            poster_rels = poster_dataset_rel_repo.find_by_dataset_id(d.id)
            for rel in poster_rels:
                poster = poster_repo.find_by_id(rel.poster_id)
                if poster:
                    citing_posters.append({
                        "id": poster.id,
                        "title": poster.title,
                        "authors": poster.authors
                    })

            datasets_summary.append({
                "id": d.id,
                "name": d.name,
                "description": d.description,
                "summary": d.summary[:200] + "..." if d.summary and len(d.summary) > 200 else d.summary,
                "file_count": d.file_count,
                "total_size": d.total_size,
                "total_size_mb": round(d.total_size / (1024 * 1024), 2) if d.total_size else 0,
                "cited_by_papers": citing_papers,
                "cited_by_posters": citing_posters,
                "drive_url": d.drive_url
            })
        
        return {
            "papers": {
                "count": len(papers),
                "items": papers_summary
            },
            "posters": {
                "count": len(posters),
                "items": posters_summary
            },
            "datasets": {
                "count": len(datasets),
                "items": datasets_summary
            },
            "totals": {
                "papers": len(papers),
                "posters": len(posters),
                "datasets": len(datasets),
                "total_items": len(papers) + len(posters) + len(datasets),
                "total_dataset_files": sum(d.file_count for d in datasets),
                "total_dataset_size_mb": round(sum(d.total_size for d in datasets) / (1024 * 1024), 2)
            }
        }
        
    except Exception as e:
        logger.error(f"データベース要約取得エラー: {e}")
        raise HTTPException(status_code=500, detail=f"データベース要約取得エラー: {str(e)}")

@app.get("/api/google-drive/status")
async def google_drive_status():
    """Google Drive状態確認API"""
    if 'default' not in user_credentials:
        return {"enabled": False, "message": "Google認証が必要です"}

    try:
        # Google Drive APIサービスを作成
        creds = user_credentials['default']
        service = build('drive', 'v3', credentials=creds)

        # フォルダ情報取得
        folder_id = os.getenv('GOOGLE_DRIVE_FOLDER_ID')
        if folder_id:
            results = service.files().list(
                q=f"'{folder_id}' in parents and trashed=false",
                pageSize=100,
                fields="files(id, name, mimeType)"
            ).execute()
            files = results.get('files', [])
        else:
            files = []

        return {
            "enabled": True,
            "file_count": len(files),
            "folders": [f["name"] for f in files if f.get('mimeType') == 'application/vnd.google-apps.folder']
        }
        
    except Exception as e:
        logger.error(f"Google Drive状態取得エラー: {e}")
        return {"enabled": True, "error": str(e)}

@app.post("/api/looker-studio/export", response_model=LookerExportResponse)
async def export_for_looker_studio(request: LookerExportRequest):
    """Looker Studio用データをGoogle Driveにエクスポート"""
    try:
        if request.export_type != "summary":
            return LookerExportResponse(
                success=False,
                message="Phase 1ではsummaryエクスポートのみ対応しています"
            )
        
        # エクスポート実行
        result = await looker_exporter.export_to_drive()
        
        return LookerExportResponse(
            success=result['success'],
            message=result['message'],
            file_id=result.get('file_id'),
            stats=result.get('stats')
        )
        
    except Exception as e:
        logger.error(f"Looker export error: {e}")
        return LookerExportResponse(
            success=False,
            message=f"エクスポートエラー: {str(e)}"
        )

@app.get("/api/looker-studio/status")
async def get_looker_export_status():
    """Looker Studioエクスポートの状態を確認"""
    try:
        # OAuth認証状態を確認
        gdrive_enabled = 'default' in user_credentials

        # 最新の統計情報を直接収集
        from agent.source.integrations.looker_export import LookerDataExporter
        exporter = LookerDataExporter(google_drive_integration=None)
        stats = exporter.collect_summary_statistics()

        return {
            'google_drive_enabled': gdrive_enabled,
            'export_available': gdrive_enabled,
            'last_stats': stats,
            'dataset_folder': 'dataset',
            'export_format': 'CSV'
        }

    except Exception as e:
        logger.error(f"Status check error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            'google_drive_enabled': False,
            'export_available': False,
            'error': str(e),
            'last_stats': {}
        }

# ==================== Google OAuth エンドポイント ====================

@app.get("/api/auth/google/login")
async def google_login():
    """Google OAuth認証を開始"""
    try:
        # credentials.jsonを読み込み
        credentials_path = os.getenv('GOOGLE_DRIVE_CREDENTIALS_PATH', 'credentials/google_drive_credentials.json')
        logger.info(f"Loading credentials from: {credentials_path}")
        logger.info(f"Absolute path: {os.path.abspath(credentials_path)}")

        if not os.path.exists(credentials_path):
            raise HTTPException(status_code=500, detail="Google credentials file not found")

        # JSONファイルを読み込んで設定を取得
        with open(credentials_path, 'r') as f:
            full_config = json.load(f)
            logger.info(f"Loaded config keys: {list(full_config.keys())}")
            # "web" または "installed" キーを取り出す
            if 'web' in full_config:
                client_config = full_config
            elif 'installed' in full_config:
                client_config = full_config
            else:
                raise ValueError(f"Invalid client secrets format. Keys found: {list(full_config.keys())}")

        # OAuth フローを作成
        flow = Flow.from_client_config(
            client_config,
            scopes=['https://www.googleapis.com/auth/drive.readonly'],
            redirect_uri=f"http://localhost:8000/api/auth/google/callback"
        )

        # 状態トークンを生成
        state = secrets.token_urlsafe(32)
        oauth_sessions[state] = {'timestamp': datetime.now()}

        # 認証URLを生成
        authorization_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            state=state
        )

        logger.info(f"Generated auth URL: {authorization_url}")

        return JSONResponse({
            'auth_url': authorization_url
        })

    except Exception as e:
        import traceback
        logger.error(f"Google login error: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/auth/google/callback")
async def google_callback(request: Request, code: str = None, state: str = None, error: str = None):
    """Google OAuth コールバック"""
    try:
        if error:
            logger.error(f"OAuth error: {error}")
            return RedirectResponse(url="/?auth_error=" + error)

        if not code or not state:
            raise HTTPException(status_code=400, detail="Missing code or state")

        # 状態トークンを検証
        if state not in oauth_sessions:
            raise HTTPException(status_code=400, detail="Invalid state token")

        # credentials.jsonを読み込み
        credentials_path = os.getenv('GOOGLE_DRIVE_CREDENTIALS_PATH', 'credentials/google_drive_credentials.json')

        # JSONファイルを読み込んで設定を取得
        with open(credentials_path, 'r') as f:
            full_config = json.load(f)
            # "web" または "installed" キーを取り出す
            if 'web' in full_config:
                client_config = full_config
            elif 'installed' in full_config:
                client_config = full_config
            else:
                raise ValueError("Invalid client secrets format")

        # OAuth フローを作成
        flow = Flow.from_client_config(
            client_config,
            scopes=['https://www.googleapis.com/auth/drive.readonly'],
            redirect_uri=f"http://localhost:8000/api/auth/google/callback",
            state=state
        )

        # 認証コードをトークンに交換
        flow.fetch_token(code=code)

        # 認証情報を保存
        creds = flow.credentials
        user_credentials['default'] = creds
        save_credentials(creds)  # ファイルに永続化

        # セッションをクリア
        del oauth_sessions[state]

        logger.info("Google Drive authentication successful")
        return RedirectResponse(url="/?auth_success=true")

    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        return RedirectResponse(url="/?auth_error=" + str(e))


@app.get("/api/auth/google/status")
async def google_auth_status():
    """Google認証状態を確認"""
    try:
        logger.info(f"Checking auth status. user_credentials keys: {list(user_credentials.keys())}")
        if 'default' in user_credentials:
            creds = user_credentials['default']
            logger.info(f"User authenticated. Creds type: {type(creds)}")
            return JSONResponse({
                'authenticated': True,
                'email': 'authenticated_user'
            })
        else:
            logger.info("User not authenticated")
            return JSONResponse({
                'authenticated': False
            })
    except Exception as e:
        import traceback
        logger.error(f"Auth status error: {e}")
        logger.error(traceback.format_exc())
        return JSONResponse({
            'authenticated': False,
            'error': str(e)
        })


@app.get("/api/drive/folders")
async def list_drive_folders():
    """Google Driveのフォルダ一覧を取得"""
    try:
        if 'default' not in user_credentials:
            raise HTTPException(status_code=401, detail="Not authenticated")

        creds = user_credentials['default']
        service = build('drive', 'v3', credentials=creds)

        # フォルダのみを検索
        results = service.files().list(
            q="mimeType='application/vnd.google-apps.folder' and trashed=false",
            pageSize=100,
            fields="files(id, name, parents)"
        ).execute()

        folders = results.get('files', [])

        return JSONResponse({
            'folders': [
                {
                    'id': folder['id'],
                    'name': folder['name'],
                    'parents': folder.get('parents', [])
                }
                for folder in folders
            ]
        })

    except Exception as e:
        logger.error(f"List folders error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class SetFolderRequest(BaseModel):
    folder_id: str

@app.post("/api/drive/set-folder")
async def set_drive_folder(request: SetFolderRequest):
    """同期対象のフォルダを設定"""
    try:
        # TODO: データベースまたは設定ファイルに保存
        # 現在は環境変数として設定
        os.environ['GOOGLE_DRIVE_FOLDER_ID'] = request.folder_id

        return JSONResponse({
            'success': True,
            'folder_id': request.folder_id
        })

    except Exception as e:
        logger.error(f"Set folder error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== ベクトル検索エンドポイント ====================

@app.post("/api/vector/index")
async def create_vector_index():
    """全ドキュメントのベクトルインデックスを作成"""
    try:
        if not vector_engine.is_enabled():
            response_data = {
                'success': False,
                'error': 'Vector search is not enabled. Set ENABLE_VECTOR_SEARCH=true in .env'
            }
            admin_metrics.record_event(
                "vector_index",
                "error",
                "ベクトル検索が無効のため再構築をスキップ",
                extra=response_data
            )
            return JSONResponse(response_data)

        result = vector_indexer.index_all_documents()
        admin_metrics.record_event(
            "vector_index",
            "success" if result.get('success') else "error",
            f"ベクトルインデックス再構築: {result.get('indexed_count', 0)}件処理",
            extra=result
        )
        return JSONResponse(result)

    except Exception as e:
        logger.error(f"Vector indexing error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        response_data = {
            'success': False,
            'error': str(e)
        }
        admin_metrics.record_event(
            "vector_index",
            "error",
            f"ベクトルインデックス再構築エラー: {str(e)}",
            extra=response_data
        )
        return JSONResponse(response_data)


@app.get("/api/vector/status")
async def get_vector_search_status():
    """ベクトル検索の状態を確認"""
    try:
        stats = vector_indexer.get_index_stats()
        return JSONResponse(stats)

    except Exception as e:
        logger.error(f"Vector status error: {e}")
        return JSONResponse({
            'enabled': False,
            'error': str(e)
        })


@app.post("/api/vector/search")
async def vector_semantic_search(request: dict):
    """セマンティック検索を実行"""
    try:
        query = request.get('query', '')
        limit = request.get('limit', 5)
        threshold = request.get('threshold', 0.7)

        if not query:
            raise HTTPException(status_code=400, detail="Query is required")

        if not vector_engine.is_enabled():
            return JSONResponse({
                'success': False,
                'results': [],
                'error': 'Vector search is not enabled'
            })

        results = vector_engine.search_similar(query, limit=limit, threshold=threshold)

        return JSONResponse({
            'success': True,
            'query': query,
            'results': results,
            'count': len(results)
        })

    except Exception as e:
        logger.error(f"Vector search error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return JSONResponse({
            'success': False,
            'results': [],
            'error': str(e)
        })


# ==================== OpenRouterモデル管理エンドポイント ====================

@app.get("/api/models")
async def get_openrouter_models():
    """OpenRouterモデル一覧を取得"""
    try:
        models = model_sync.get_models_from_db()
        return JSONResponse({
            'success': True,
            'models': [model.to_dict() for model in models],
            'count': len(models)
        })
    except Exception as e:
        logger.error(f"モデル一覧取得エラー: {e}")
        return JSONResponse({
            'success': False,
            'models': [],
            'error': str(e)
        })


@app.post("/api/models/sync")
async def sync_openrouter_models():
    """OpenRouterモデル一覧を手動で同期"""
    try:
        result = model_sync.sync_models()
        admin_metrics.record_event(
            "model_sync",
            "success" if result.get('success') else "error",
            result.get('message', 'OpenRouterモデル同期を実行しました'),
            extra=result
        )
        return JSONResponse(result)
    except Exception as e:
        logger.error(f"モデル同期エラー: {e}")
        response_data = {
            'success': False,
            'message': f"同期エラー: {str(e)}"
        }
        admin_metrics.record_event(
            "model_sync",
            "error",
            f"OpenRouterモデル同期エラー: {str(e)}",
            extra=response_data
        )
        return JSONResponse(response_data)


if __name__ == "__main__":
    import uvicorn

    # 設定読み込み
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))

    uvicorn.run(app, host=host, port=port, reload=True)
