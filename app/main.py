"""
研究データ管理システム Webアプリケーション
Google Drive連携、AI検索・研究相談機能付き
"""

import asyncio
import json
import os
import secrets
import sys
import threading
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.requests import Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

# 既存のコンポーネントをインポート
sys.path.append(".")

from agent.source.database.connection import db_connection
from agent.source.database.new_models import Dataset, DatasetFile, Paper, PaperDatasetRelation, Poster, PosterDatasetRelation
from services.admin_metrics import admin_metrics

from .core import (
    auth_manager,
    dataset_advisor,
    dataset_file_repo,
    dataset_repo,
    enhanced_advisor,
    google_drive,
    load_credentials,
    logger,
    llm_client,
    looker_exporter,
    model_repo,
    model_sync,
    oauth_sessions,
    paper_dataset_rel_repo,
    paper_repo,
    poster_dataset_rel_repo,
    poster_repo,
    save_credentials,
    user_credentials,
    vector_engine,
)
from .schemas import (
    ConsultationResponse,
    GoogleDriveSyncRequest,
    LookerExportRequest,
    LookerExportResponse,
    ResearchConsultationRequest,
    SearchRequest,
    SearchResponse,
    SetFolderRequest,
    SyncResponse,
)
from .routers.pages import router as pages_router

# FastAPIアプリケーション初期化
app = FastAPI(
    title="研究データ管理システム",
    description="Google Drive連携とAI研究相談機能を備えた研究データ管理システム",
    version="1.0.0",
)

# 静的ファイルとテンプレート設定
app.mount("/static", StaticFiles(directory="static"), name="static")

# ルーター登録
app.include_router(pages_router)


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
    
    if vector_engine.is_enabled():
        try:
            await vector_engine.initialize()
            logger.info("ベクトル検索サービスを初期化しました")
        except Exception as e:
            logger.error(f"ベクトル検索初期化エラー: {e}")

    logger.info("研究データ管理システム Webアプリ起動完了")

@app.post("/api/sync/google-drive", response_model=SyncResponse)
async def sync_google_drive(request: GoogleDriveSyncRequest, background_tasks: BackgroundTasks):
    """Google Drive同期API"""
    # 認証情報がない場合、トークンファイルから再読み込み
    if 'default' not in user_credentials:
        logger.info("認証情報が見つかりません。トークンファイルを再読み込みします...")
        load_credentials()

    # 再読み込み後も認証情報がない場合はエラー
    if 'default' not in user_credentials:
        raise HTTPException(status_code=401, detail="Google認証が必要です")

    try:
        # 同期対象フォルダIDをリストに正規化
        raw_folder_ids = (request.folder_ids or []) + ([request.folder_id] if request.folder_id else [])
        folder_ids = []
        seen_ids = set()
        for fid in raw_folder_ids:
            if fid and fid not in seen_ids:
                folder_ids.append(fid)
                seen_ids.add(fid)

        # バックグラウンドで同期実行
        background_tasks.add_task(perform_google_drive_sync, request.folder_type, folder_ids)

        return SyncResponse(
            success=True,
            message="Google Drive同期を開始しました",
            files_processed=0
        )
    except Exception as e:
        logger.error(f"Google Drive同期エラー: {e}")
        raise HTTPException(status_code=500, detail=f"同期エラー: {str(e)}")

async def perform_google_drive_sync(folder_type: str, folder_ids: List[str]):
    """Google Drive同期の実際の処理"""
    try:
        logger.info(f"Google Drive同期開始: folder_type={folder_type}, folder_ids={folder_ids}")

        if 'default' not in user_credentials:
            logger.error("認証情報がありません")
            return

        # Google Drive APIサービスを作成
        creds = user_credentials['default']
        service = build('drive', 'v3', credentials=creds)

        # フォルダIDが渡されていない場合は環境変数から取得
        normalized_folder_ids = list(folder_ids or [])
        if not normalized_folder_ids:
            env_ids = os.getenv('GOOGLE_DRIVE_FOLDER_IDS')
            if env_ids:
                try:
                    parsed = json.loads(env_ids)
                    if isinstance(parsed, list):
                        normalized_folder_ids.extend([fid for fid in parsed if isinstance(fid, str) and fid])
                except json.JSONDecodeError:
                    normalized_folder_ids.extend([fid.strip() for fid in env_ids.split(',') if fid.strip()])

        # 後方互換のため単一フォルダ設定も参照
        single_env = os.getenv('GOOGLE_DRIVE_FOLDER_ID')
        if single_env and single_env not in normalized_folder_ids:
            normalized_folder_ids.append(single_env)

        # 重複と空文字を除外
        deduped_ids: List[str] = []
        seen_id_set = set()
        for fid in normalized_folder_ids:
            if not fid:
                continue
            if fid in seen_id_set:
                continue
            deduped_ids.append(fid)
            seen_id_set.add(fid)
        normalized_folder_ids = deduped_ids

        if not normalized_folder_ids:
            logger.error("同期対象フォルダが設定されていません")
            return

        total_files_processed = 0
        aggregated_errors: List[str] = []
        processed_folders: List[str] = []

        for root_folder_id in normalized_folder_ids:
            files_processed, errors = await sync_root_folder_contents(folder_type, root_folder_id, service)
            total_files_processed += files_processed
            if errors:
                aggregated_errors.extend([f"[{root_folder_id}] {err}" for err in errors])
            processed_folders.append(root_folder_id)

        logger.info(
            f"Google Drive同期完了: {total_files_processed}ファイル処理, "
            f"{len(aggregated_errors)}エラー, 対象フォルダ: {processed_folders}"
        )

        # 統計情報を更新（キャッシュクリア効果）
        stats = {
            "papers": len(paper_repo.find_all()),
            "posters": len(poster_repo.find_all()),
            "datasets": len(dataset_repo.find_all())
        }
        logger.info(
            f"同期後統計: 論文{stats['papers']}件, "
            f"ポスター{stats['posters']}件, データセット{stats['datasets']}件"
        )

        admin_metrics.record_event(
            "drive_sync",
            "success" if not aggregated_errors else "partial",
            f"Google Drive同期完了: {total_files_processed}件処理 (エラー{len(aggregated_errors)}件)",
            extra={
                "folder_type": folder_type,
                "folder_ids": processed_folders,
                "files_processed": total_files_processed,
                "error_count": len(aggregated_errors),
                "errors": aggregated_errors[:10]
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
                "folder_ids": folder_ids,
                "error": str(e)
            }
        )


async def sync_root_folder_contents(folder_type: str, root_folder_id: str, service) -> Tuple[int, List[str]]:
    """指定したルートフォルダ以下のファイル群を同期"""
    logger.info(f"同期対象フォルダ処理開始: {root_folder_id}")

    results = service.files().list(
        q=f"'{root_folder_id}' in parents and trashed=false",
        pageSize=100,
        fields="files(id, name, mimeType, parents)"
    ).execute()

    child_entries = results.get('files', [])
    files_processed = 0
    errors: List[str] = []

    # フェーズ1: データセットを先に処理（cited_datasetsの参照先を作成）
    logger.info("Phase 1: データセットの処理開始")
    if folder_type in ["all", "datasets"]:
        # child_entriesから「datasets」フォルダを探す
        for entry in child_entries:
            if entry.get('mimeType') != 'application/vnd.google-apps.folder':
                continue

            entry_name = entry['name']
            entry_id = entry['id']

            # datasetsフォルダのみを処理
            if entry_name == 'datasets':
                logger.info(f"datasetsフォルダ発見: {entry_id}")
                nested_results = service.files().list(
                    q=f"'{entry_id}' in parents and trashed=false",
                    pageSize=100,
                    fields="files(id, name, mimeType, parents)"
                ).execute()
                nested_items = nested_results.get('files', [])
                logger.info(f"datasetsフォルダ内のアイテム数: {len(nested_items)}")
                dataset_files_count = await process_datasets_folder(nested_items, service)
                files_processed += dataset_files_count
                break
    elif folder_type == "dataset":
        # 指定タイプのみ処理
        for entry in child_entries:
            if entry.get('mimeType') != 'application/vnd.google-apps.folder':
                continue

            entry_name = entry['name']
            entry_id = entry['id']

            if entry_name == 'datasets':
                nested_results = service.files().list(
                    q=f"'{entry_id}' in parents and trashed=false",
                    pageSize=100,
                    fields="files(id, name, mimeType, parents)"
                ).execute()
                nested_items = nested_results.get('files', [])
                dataset_files_count = await process_datasets_folder(nested_items, service)
                files_processed += dataset_files_count

    # フェーズ2: 論文・ポスターを処理（cited_datasetsの関連を作成）
    logger.info("Phase 2: 論文・ポスターの処理開始")
    for entry in child_entries:
        if entry.get('mimeType') != 'application/vnd.google-apps.folder':
            continue

        entry_name = entry['name']
        child_folder_id = entry['id']

        if folder_type != "all" and entry_name not in [folder_type, f"{folder_type}s"]:
            continue

        nested_results = service.files().list(
            q=f"'{child_folder_id}' in parents and trashed=false",
            pageSize=100,
            fields="files(id, name, mimeType, parents)"
        ).execute()
        files_in_folder = nested_results.get('files', [])

        if entry_name != 'datasets':
            for file in files_in_folder:
                if file.get('mimeType') == 'application/vnd.google-apps.folder':
                    continue
                try:
                    await process_drive_file(file, entry_name, service)
                    files_processed += 1
                except Exception as e:
                    errors.append(f"{file['name']}: {str(e)}")

    return files_processed, errors

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
            file_analyses = {}  # ファイルID -> 解析結果のマッピング

            # ファイル情報を収集
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
                        file_analyses[file_info['id']] = file_analysis
            
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

                    # 新規作成後、existing_datasetを設定
                    existing_dataset = dataset_repo.find_by_name(dataset_name)

                # データセット作成/更新後、全ファイルをDatasetFileテーブルに登録
                if existing_dataset:
                    for file_info in dataset_file_list:
                        file_path = f"gdrive://dataset/{dataset_name}/{file_info['id']}"
                        existing_file = dataset_file_repo.find_by_path(file_path)

                        extension = file_info['name'].split('.')[-1].lower() if '.' in file_info['name'] else ''
                        drive_url = f"https://drive.google.com/file/d/{file_info['id']}/view"

                        # 解析結果を取得（存在する場合）
                        file_analysis = file_analyses.get(file_info['id'], {'schema_info': None, 'summary': None})

                        if existing_file:
                            # 既存ファイルの更新
                            needs_file_update = False

                            if file_analysis['schema_info']:
                                existing_file.schema_info = file_analysis['schema_info']
                                existing_file.summary = file_analysis['summary']
                                needs_file_update = True

                            if not existing_file.drive_url:
                                existing_file.drive_url = drive_url
                                existing_file.drive_file_id = file_info['id']
                                needs_file_update = True

                            if needs_file_update:
                                dataset_file_repo.update(existing_file)
                                logger.info(f"データセットファイル情報更新: {file_info['name']}")
                        else:
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
                needs_update = False

                if metadata.get('title') and metadata.get('title') != existing_paper.title:
                    existing_paper.title = metadata.get('title', existing_paper.title)
                    needs_update = True
                if metadata.get('authors'):
                    existing_paper.authors = metadata.get('authors', existing_paper.authors)
                    needs_update = True
                if metadata.get('abstract'):
                    existing_paper.abstract = metadata.get('abstract', existing_paper.abstract)
                    needs_update = True
                if metadata.get('keywords'):
                    existing_paper.keywords = metadata.get('keywords', existing_paper.keywords)
                    needs_update = True

                # drive_url が無い場合は追加
                if not existing_paper.drive_url:
                    drive_url = f"https://drive.google.com/file/d/{file_info['id']}/view"
                    existing_paper.drive_url = drive_url
                    existing_paper.drive_file_id = file_info['id']
                    needs_update = True
                    logger.info(f"drive_url を設定: {file_info['name']}")

                if needs_update:
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
                needs_update = False

                if metadata.get('title') and metadata.get('title') != existing_poster.title:
                    existing_poster.title = metadata.get('title', existing_poster.title)
                    needs_update = True
                if metadata.get('authors'):
                    existing_poster.authors = metadata.get('authors', existing_poster.authors)
                    needs_update = True
                if metadata.get('abstract'):
                    existing_poster.abstract = metadata.get('abstract', existing_poster.abstract)
                    needs_update = True
                if metadata.get('keywords'):
                    existing_poster.keywords = metadata.get('keywords', existing_poster.keywords)
                    needs_update = True

                # drive_url が無い場合は追加
                if not existing_poster.drive_url:
                    drive_url = f"https://drive.google.com/file/d/{file_info['id']}/view"
                    existing_poster.drive_url = drive_url
                    existing_poster.drive_file_id = file_info['id']
                    needs_update = True
                    logger.info(f"drive_url を設定: {file_info['name']}")

                if needs_update:
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
        result = await enhanced_advisor.research_consultation(
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
        configured_ids: List[str] = []
        env_ids = os.getenv('GOOGLE_DRIVE_FOLDER_IDS')
        if env_ids:
            try:
                parsed = json.loads(env_ids)
                if isinstance(parsed, list):
                    configured_ids.extend([fid for fid in parsed if isinstance(fid, str) and fid])
            except json.JSONDecodeError:
                configured_ids.extend([fid.strip() for fid in env_ids.split(',') if fid.strip()])

        single_env = os.getenv('GOOGLE_DRIVE_FOLDER_ID')
        if single_env and single_env not in configured_ids:
            configured_ids.append(single_env)

        child_folder_names: List[str] = []
        total_children = 0
        selected_folders: List[Dict[str, str]] = []

        for folder_id in configured_ids:
            folder_display_name = folder_id
            try:
                metadata = service.files().get(
                    fileId=folder_id,
                    fields="id, name"
                ).execute()
                folder_display_name = metadata.get('name', folder_id)
            except Exception as e:
                logger.warning(f"フォルダ情報取得に失敗: {folder_id}: {e}")

            selected_folders.append({
                "id": folder_id,
                "name": folder_display_name
            })

            try:
                results = service.files().list(
                    q=f"'{folder_id}' in parents and trashed=false",
                    pageSize=100,
                    fields="files(id, name, mimeType)"
                ).execute()
                files = results.get('files', [])
                total_children += len(files)
                child_folder_names.extend([
                    f["name"] for f in files
                    if f.get('mimeType') == 'application/vnd.google-apps.folder'
                ])
            except Exception as e:
                logger.warning(f"フォルダ配下の取得に失敗: {folder_id}: {e}")

        return {
            "enabled": True,
            "file_count": total_children,
            "folders": child_folder_names,
            "configured_folder_ids": configured_ids,
            "selected_folders": selected_folders
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

        # トークンファイルから再読み込み
        if 'default' not in user_credentials:
            logger.info("認証情報が見つかりません。トークンファイルを再読み込みします...")
            load_credentials()

        if 'default' in user_credentials:
            creds = user_credentials['default']
            logger.info(f"User authenticated. Creds type: {type(creds)}")

            # トークンの有効性チェックとリフレッシュ
            try:
                if hasattr(creds, 'expired') and hasattr(creds, 'refresh_token'):
                    if creds.expired and creds.refresh_token:
                        logger.info("トークンが期限切れです。リフレッシュします...")
                        from google.auth.transport.requests import Request
                        creds.refresh(Request())
                        save_credentials(creds)
                        user_credentials['default'] = creds
                        logger.info("トークンリフレッシュ完了")
            except Exception as refresh_error:
                logger.warning(f"トークンリフレッシュエラー: {refresh_error}")
                # リフレッシュ失敗しても、トークンが有効な可能性があるので続行

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


@app.post("/api/drive/set-folder")
async def set_drive_folder(request: SetFolderRequest):
    """同期対象のフォルダを設定"""
    try:
        requested_ids = (request.folder_ids or []) + ([request.folder_id] if request.folder_id else [])
        normalized_ids: List[str] = []
        seen = set()
        for fid in requested_ids:
            if not fid or fid in seen:
                continue
            normalized_ids.append(fid)
            seen.add(fid)

        if normalized_ids:
            # TODO: データベースまたは設定ファイルに保存
            os.environ['GOOGLE_DRIVE_FOLDER_IDS'] = json.dumps(normalized_ids)
            os.environ['GOOGLE_DRIVE_FOLDER_ID'] = normalized_ids[0]
        else:
            os.environ.pop('GOOGLE_DRIVE_FOLDER_IDS', None)
            os.environ.pop('GOOGLE_DRIVE_FOLDER_ID', None)

        return JSONResponse({
            'success': True,
            'folder_ids': normalized_ids,
            'primary_folder_id': normalized_ids[0] if normalized_ids else None
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
                'error': 'Vector search is not enabled. Set VECTOR_SEARCH_ENABLED=true (or ENABLE_VECTOR_SEARCH=true) in .env'
            }
            admin_metrics.record_event(
                "vector_index",
                "error",
                "ベクトル検索が無効のため再構築をスキップ",
                extra=response_data
            )
            return JSONResponse(response_data)

        result = await vector_engine.index_all_documents()
        success = result.get('success', False)
        message = result.get('message') or (
            f"Indexed {result.get('successful', 0)}/{result.get('total_documents', 0)} documents"
        )
        response = {
            **result,
            'success': success,
            'message': message,
        }
        admin_metrics.record_event(
            "vector_index",
            "success" if success else "error",
            f"ベクトルインデックス再構築: {message}",
            extra=response
        )
        return JSONResponse(response)

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
        status = await vector_engine.get_service_status()
        return JSONResponse(status)

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

        results = await vector_engine.vector_search(
            query=query,
            top_k=limit,
            similarity_threshold=threshold
        )

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
async def get_openrouter_models(include_hidden: bool = False):
    """OpenRouterモデル一覧を取得"""
    try:
        models = model_sync.get_models_from_db(include_hidden=include_hidden)
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


# ==================== データセットプレビューエンドポイント ====================

@app.get("/api/datasets/{dataset_id}")
async def get_dataset_detail(dataset_id: int):
    """データセット詳細情報を取得"""
    try:
        dataset = dataset_repo.find_by_id(dataset_id)
        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")

        # データセット内のファイル一覧を取得
        files = dataset_file_repo.find_by_dataset_id(dataset_id)

        # 引用している論文・ポスターを取得
        citing_papers = []
        paper_rels = paper_dataset_rel_repo.find_by_dataset_id(dataset_id)
        for rel in paper_rels:
            paper = paper_repo.find_by_id(rel.paper_id)
            if paper:
                citing_papers.append({
                    "id": paper.id,
                    "title": paper.title,
                    "authors": paper.authors,
                    "file_name": paper.file_name
                })

        citing_posters = []
        poster_rels = poster_dataset_rel_repo.find_by_dataset_id(dataset_id)
        for rel in poster_rels:
            poster = poster_repo.find_by_id(rel.poster_id)
            if poster:
                citing_posters.append({
                    "id": poster.id,
                    "title": poster.title,
                    "authors": poster.authors,
                    "file_name": poster.file_name
                })

        # ファイル情報を整形
        files_info = []
        for file in files:
            file_info = {
                "id": file.id,
                "file_name": file.file_name,
                "file_type": file.file_type,
                "file_size": file.file_size,
                "file_size_mb": round(file.file_size / (1024 * 1024), 2) if file.file_size else 0,
                "summary": file.summary,
                "schema_info": json.loads(file.schema_info) if file.schema_info else None,
                "drive_file_id": file.drive_file_id,
                "drive_url": file.drive_url,
                "created_at": file.created_at.isoformat() if file.created_at else None,
                "updated_at": file.updated_at.isoformat() if file.updated_at else None
            }
            files_info.append(file_info)

        return JSONResponse({
            "success": True,
            "dataset": {
                "id": dataset.id,
                "name": dataset.name,
                "description": dataset.description,
                "summary": dataset.summary,
                "file_count": dataset.file_count,
                "total_size": dataset.total_size,
                "total_size_mb": round(dataset.total_size / (1024 * 1024), 2) if dataset.total_size else 0,
                "drive_folder_id": dataset.drive_folder_id,
                "drive_url": dataset.drive_url,
                "created_at": dataset.created_at.isoformat() if dataset.created_at else None,
                "updated_at": dataset.updated_at.isoformat() if dataset.updated_at else None
            },
            "files": files_info,
            "citing_papers": citing_papers,
            "citing_posters": citing_posters
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Dataset detail error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/datasets/{dataset_id}/files")
async def get_dataset_files(dataset_id: int):
    """データセット内のファイル一覧を取得"""
    try:
        dataset = dataset_repo.find_by_id(dataset_id)
        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")

        files = dataset_file_repo.find_by_dataset_id(dataset_id)

        files_info = []
        for file in files:
            files_info.append({
                "id": file.id,
                "file_name": file.file_name,
                "file_type": file.file_type,
                "file_size": file.file_size,
                "file_size_mb": round(file.file_size / (1024 * 1024), 2) if file.file_size else 0,
                "summary": file.summary,
                "drive_file_id": file.drive_file_id,
                "drive_url": file.drive_url
            })

        return JSONResponse({
            "success": True,
            "dataset_id": dataset_id,
            "dataset_name": dataset.name,
            "files": files_info,
            "count": len(files_info)
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Dataset files error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/datasets/{dataset_id}/files/{file_id}/preview")
async def get_file_preview(dataset_id: int, file_id: int, rows: int = 100):
    """データセットファイルのプレビューを取得"""
    try:
        # 認証確認
        if 'default' not in user_credentials:
            raise HTTPException(status_code=401, detail="Google認証が必要です")

        # ファイル情報を取得
        file = dataset_file_repo.find_by_path(f"gdrive://dataset/%/{file_id}")
        if not file:
            # IDで直接検索
            all_files = dataset_file_repo.find_by_dataset_id(dataset_id)
            file = next((f for f in all_files if f.id == file_id), None)

        if not file or file.dataset_id != dataset_id:
            raise HTTPException(status_code=404, detail="File not found")

        # Google Drive APIサービスを作成
        creds = user_credentials['default']
        service = build('drive', 'v3', credentials=creds)

        # ファイルをダウンロードしてプレビュー生成
        preview_data = await generate_file_preview(
            service,
            file.drive_file_id,
            file.file_name,
            file.file_type,
            rows
        )

        return JSONResponse({
            "success": True,
            "file_id": file_id,
            "file_name": file.file_name,
            "file_type": file.file_type,
            "preview": preview_data
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File preview error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


async def generate_file_preview(service, file_id: str, file_name: str, file_type: str, max_rows: int = 100) -> Dict[str, Any]:
    """ファイルのプレビューデータを生成"""
    try:
        import tempfile
        import pandas as pd
        from googleapiclient.http import MediaIoBaseDownload
        import io

        # 一時ファイルを作成
        with tempfile.NamedTemporaryFile(suffix=f'.{file_type}', delete=False) as tmp_file:
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
            preview_data = {}

            if file_type == 'csv':
                # CSVファイルの解析
                df = pd.read_csv(tmp_path, nrows=max_rows)

                # データプレビュー
                preview_data['columns'] = list(df.columns)
                preview_data['total_rows'] = len(df)
                preview_data['dtypes'] = {col: str(dtype) for col, dtype in df.dtypes.items()}

                # inf/-inf/NaN をNoneに置換（JSON互換性のため）
                import numpy as np
                import math

                def clean_value(val):
                    """JSON互換性のためにinf/NaN/naをNoneに変換"""
                    if val is None:
                        return None
                    if isinstance(val, float):
                        if math.isnan(val) or math.isinf(val):
                            return None
                    return val

                rows = df.to_dict(orient='records')
                preview_data['rows'] = [
                    {k: clean_value(v) for k, v in row.items()}
                    for row in rows
                ]

                # 統計情報
                stats = {}
                for col in df.columns:
                    # unique_count の計算（ハッシュ化できない型の場合はスキップ）
                    try:
                        unique_count = int(df[col].nunique())
                    except (TypeError, AttributeError):
                        # dict, list など unhashable type の場合
                        unique_count = -1

                    col_stats = {
                        'type': str(df[col].dtype),
                        'null_count': int(df[col].isnull().sum()),
                        'unique_count': unique_count
                    }

                    # 数値型の場合は統計情報を追加
                    if pd.api.types.is_numeric_dtype(df[col]):
                        import math
                        import warnings

                        # 空のカラムの警告を抑制
                        with warnings.catch_warnings():
                            warnings.simplefilter("ignore", category=RuntimeWarning)
                            min_val = float(df[col].min()) if not pd.isna(df[col].min()) else None
                            max_val = float(df[col].max()) if not pd.isna(df[col].max()) else None
                            mean_val = float(df[col].mean()) if not pd.isna(df[col].mean()) else None
                            median_val = float(df[col].median()) if not pd.isna(df[col].median()) else None

                        # inf/-inf をNoneに変換
                        col_stats['min'] = min_val if min_val is not None and math.isfinite(min_val) else None
                        col_stats['max'] = max_val if max_val is not None and math.isfinite(max_val) else None
                        col_stats['mean'] = mean_val if mean_val is not None and math.isfinite(mean_val) else None
                        col_stats['median'] = median_val if median_val is not None and math.isfinite(median_val) else None

                    stats[col] = col_stats

                preview_data['statistics'] = stats

            elif file_type in ['json', 'jsonl']:
                if file_type == 'jsonl':
                    # JSONLファイルの解析
                    with open(tmp_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()[:max_rows]
                        data = [json.loads(line) for line in lines]

                    preview_data['format'] = 'jsonl'
                    preview_data['total_rows'] = len(lines)

                    if data:
                        # 最初のレコードからカラムを抽出
                        preview_data['columns'] = list(data[0].keys()) if isinstance(data[0], dict) else []

                        # DataFrameに変換して統計情報を生成
                        df = pd.DataFrame(data)

                        # inf/-inf/NaN をNoneに置換（JSON互換性のため）
                        import numpy as np
                        import math

                        def clean_value(val):
                            """JSON互換性のためにinf/NaN/naをNoneに変換"""
                            if val is None:
                                return None
                            if isinstance(val, float):
                                if math.isnan(val) or math.isinf(val):
                                    return None
                            return val

                        rows = df.to_dict(orient='records')
                        preview_data['rows'] = [
                            {k: clean_value(v) for k, v in row.items()}
                            for row in rows
                        ]

                        # 統計情報を生成
                        stats = {}
                        for col in df.columns:
                            # unique_count の計算（ハッシュ化できない型の場合はスキップ）
                            try:
                                unique_count = int(df[col].nunique())
                            except (TypeError, AttributeError):
                                # dict, list など unhashable type の場合
                                unique_count = -1

                            col_stats = {
                                'type': str(df[col].dtype),
                                'null_count': int(df[col].isnull().sum()),
                                'unique_count': unique_count
                            }

                            # 数値型の場合は統計情報を追加
                            if pd.api.types.is_numeric_dtype(df[col]):
                                import warnings

                                # 空のカラムの警告を抑制
                                with warnings.catch_warnings():
                                    warnings.simplefilter("ignore", category=RuntimeWarning)
                                    min_val = float(df[col].min()) if not pd.isna(df[col].min()) else None
                                    max_val = float(df[col].max()) if not pd.isna(df[col].max()) else None
                                    mean_val = float(df[col].mean()) if not pd.isna(df[col].mean()) else None
                                    median_val = float(df[col].median()) if not pd.isna(df[col].median()) else None

                                # inf/-inf をNoneに変換
                                col_stats['min'] = min_val if min_val is not None and math.isfinite(min_val) else None
                                col_stats['max'] = max_val if max_val is not None and math.isfinite(max_val) else None
                                col_stats['mean'] = mean_val if mean_val is not None and math.isfinite(mean_val) else None
                                col_stats['median'] = median_val if median_val is not None and math.isfinite(median_val) else None

                            stats[col] = col_stats

                        preview_data['statistics'] = stats
                    else:
                        preview_data['rows'] = data
                else:
                    # JSONファイルの解析
                    with open(tmp_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    if isinstance(data, list):
                        preview_data['format'] = 'json_array'
                        preview_data['total_rows'] = min(len(data), max_rows)

                        if data and isinstance(data[0], dict):
                            preview_data['columns'] = list(data[0].keys())

                            # DataFrameに変換して統計情報を生成
                            df = pd.DataFrame(data[:max_rows])

                            # inf/-inf/NaN をNoneに置換（JSON互換性のため）
                            import numpy as np
                            import math

                            def clean_value(val):
                                if val is None:
                                    return None
                                if isinstance(val, float):
                                    if math.isnan(val) or math.isinf(val):
                                        return None
                                return val

                            rows = df.to_dict(orient='records')
                            preview_data['rows'] = [
                                {k: clean_value(v) for k, v in row.items()}
                                for row in rows
                            ]

                            # 統計情報を生成
                            stats = {}
                            for col in df.columns:
                                # unique_count の計算（ハッシュ化できない型の場合はスキップ）
                                try:
                                    unique_count = int(df[col].nunique())
                                except (TypeError, AttributeError):
                                    # dict, list など unhashable type の場合
                                    unique_count = -1

                                col_stats = {
                                    'type': str(df[col].dtype),
                                    'null_count': int(df[col].isnull().sum()),
                                    'unique_count': unique_count
                                }

                                if pd.api.types.is_numeric_dtype(df[col]):
                                    import warnings
                                    with warnings.catch_warnings():
                                        warnings.simplefilter("ignore", category=RuntimeWarning)
                                        min_val = float(df[col].min()) if not pd.isna(df[col].min()) else None
                                        max_val = float(df[col].max()) if not pd.isna(df[col].max()) else None
                                        mean_val = float(df[col].mean()) if not pd.isna(df[col].mean()) else None
                                        median_val = float(df[col].median()) if not pd.isna(df[col].median()) else None

                                    col_stats['min'] = min_val if min_val is not None and math.isfinite(min_val) else None
                                    col_stats['max'] = max_val if max_val is not None and math.isfinite(max_val) else None
                                    col_stats['mean'] = mean_val if mean_val is not None and math.isfinite(mean_val) else None
                                    col_stats['median'] = median_val if median_val is not None and math.isfinite(median_val) else None

                                stats[col] = col_stats

                            preview_data['statistics'] = stats
                        else:
                            preview_data['rows'] = data[:max_rows]
                    else:
                        preview_data['format'] = 'json_object'
                        preview_data['data'] = data
                        if isinstance(data, dict):
                            preview_data['columns'] = list(data.keys())

            return preview_data

        finally:
            # 一時ファイルを削除
            try:
                os.remove(tmp_path)
            except:
                pass

    except Exception as e:
        logger.error(f"Preview generation error: {file_name}, {e}")
        raise


if __name__ == "__main__":
    import uvicorn

    # 設定読み込み
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))

    uvicorn.run(app, host=host, port=port, reload=True)
