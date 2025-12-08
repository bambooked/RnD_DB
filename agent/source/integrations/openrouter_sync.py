"""
OpenRouterモデル一覧の同期機能
"""
import logging
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from agent.source.database.new_repository import OpenRouterModelRepository
from agent.source.database.new_models import OpenRouterModel
from tools.config import OPENROUTER_API_KEY

logger = logging.getLogger(__name__)


class OpenRouterModelSync:
    """OpenRouterのモデル一覧を取得・同期するクラス"""

    MODELS_API_URL = "https://openrouter.ai/api/v1/models"
    UPDATE_INTERVAL_HOURS = 24  # 24時間ごとに更新

    def __init__(self):
        self.repo = OpenRouterModelRepository()
        if not OPENROUTER_API_KEY:
            logger.warning("OPENROUTER_API_KEYが設定されていません")

    def should_update(self) -> bool:
        """更新が必要かどうかを判定"""
        last_update = self.repo.get_last_update_time()
        if not last_update:
            # データベースが空の場合は更新が必要
            return True

        # 最終更新から24時間以上経過している場合は更新が必要
        time_since_update = datetime.now() - last_update
        return time_since_update > timedelta(hours=self.UPDATE_INTERVAL_HOURS)

    def fetch_models_from_api(self) -> Optional[List[Dict[str, Any]]]:
        """OpenRouter APIからモデル一覧を取得"""
        try:
            headers = {}
            if OPENROUTER_API_KEY:
                headers["Authorization"] = f"Bearer {OPENROUTER_API_KEY}"

            response = requests.get(
                self.MODELS_API_URL,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()

            data = response.json()
            models = data.get("data", [])
            logger.info(f"OpenRouter APIから{len(models)}個のモデルを取得しました")
            return models

        except requests.RequestException as e:
            logger.error(f"OpenRouter API呼び出しエラー: {e}")
            return None
        except Exception as e:
            logger.error(f"モデル一覧取得エラー: {e}")
            return None

    def parse_model_data(self, model_data: Dict[str, Any]) -> OpenRouterModel:
        """APIレスポンスからOpenRouterModelを生成"""
        model_id = model_data.get("id", "")
        model_name = model_data.get("name", model_id)
        description = model_data.get("description", "")

        # コンテキスト長の取得
        context_length = model_data.get("context_length")
        if not context_length:
            context_length = model_data.get("max_tokens")

        # 価格情報の取得
        pricing = model_data.get("pricing", {})
        pricing_prompt = None
        pricing_completion = None
        if pricing:
            # 価格は通常 "tokens per million" で提供される
            prompt_price = pricing.get("prompt")
            completion_price = pricing.get("completion")

            # 文字列の場合は数値に変換
            if isinstance(prompt_price, str):
                try:
                    pricing_prompt = float(prompt_price)
                except ValueError:
                    pricing_prompt = None
            else:
                pricing_prompt = prompt_price

            if isinstance(completion_price, str):
                try:
                    pricing_completion = float(completion_price)
                except ValueError:
                    pricing_completion = None
            else:
                pricing_completion = completion_price

        # その他の情報
        top_provider = model_data.get("top_provider", {})
        top_provider_name = None
        if isinstance(top_provider, dict):
            top_provider_name = top_provider.get("name")
        elif isinstance(top_provider, str):
            top_provider_name = top_provider

        architecture = model_data.get("architecture", {})
        architecture_str = None
        if isinstance(architecture, dict):
            architecture_str = architecture.get("tokenizer") or architecture.get("instruct_type")
        elif isinstance(architecture, str):
            architecture_str = architecture

        modality = model_data.get("modality")

        return OpenRouterModel(
            model_id=model_id,
            model_name=model_name,
            description=description,
            context_length=context_length,
            pricing_prompt=pricing_prompt,
            pricing_completion=pricing_completion,
            top_provider=top_provider_name,
            architecture=architecture_str,
            modality=modality
        )

    def sync_models(self) -> Dict[str, Any]:
        """モデル一覧を同期"""
        try:
            # APIからモデル一覧を取得
            models_data = self.fetch_models_from_api()
            if not models_data:
                return {
                    "success": False,
                    "message": "APIからモデル一覧を取得できませんでした",
                    "models_synced": 0
                }

            # データベースに保存
            synced_count = 0
            for model_data in models_data:
                try:
                    model = self.parse_model_data(model_data)
                    self.repo.upsert(model)
                    synced_count += 1
                except Exception as e:
                    logger.error(f"モデル保存エラー ({model_data.get('id')}): {e}")

            logger.info(f"モデル同期完了: {synced_count}個のモデルを保存しました")
            return {
                "success": True,
                "message": f"{synced_count}個のモデルを同期しました",
                "models_synced": synced_count,
                "total_models": self.repo.count()
            }

        except Exception as e:
            logger.error(f"モデル同期エラー: {e}")
            return {
                "success": False,
                "message": f"同期エラー: {str(e)}",
                "models_synced": 0
            }

    def get_models_from_db(self, include_hidden: bool = False) -> List[OpenRouterModel]:
        """データベースからモデル一覧を取得"""
        if include_hidden:
            return self.repo.find_all()
        return self.repo.find_visible()

    def sync_if_needed(self) -> Dict[str, Any]:
        """必要に応じてモデル一覧を同期"""
        if self.should_update():
            logger.info("モデル一覧の更新が必要です。同期を開始します...")
            return self.sync_models()
        else:
            logger.info("モデル一覧は最新です")
            return {
                "success": True,
                "message": "モデル一覧は最新です",
                "models_synced": 0,
                "total_models": self.repo.count(),
                "skipped": True
            }
