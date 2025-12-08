"""LLMクライアントファクトリー

環境変数に基づいて適切なLLMクライアントを生成するファクトリーパターン実装。
"""

import logging
from typing import Optional

from agent.source.analyzer.llm_interface import LLMClientInterface
from agent.source.analyzer.openrouter_client import OpenRouterClient
from agent.source.analyzer.openai_client import OpenAIClient
from agent.source.analyzer.gemini_client import GeminiClient

logger = logging.getLogger(__name__)


class LLMFactory:
    """LLMクライアントファクトリー"""

    @staticmethod
    def create_client(
        provider: str,
        api_key: str,
        model: Optional[str] = None,
    ) -> LLMClientInterface:
        """LLMクライアントを生成

        Args:
            provider: プロバイダー名（'openrouter', 'openai', 'gemini'）
            api_key: APIキー
            model: モデル名（省略時はプロバイダーのデフォルト）

        Returns:
            LLMClientInterface実装クラスのインスタンス

        Raises:
            ValueError: 未対応のプロバイダーが指定された場合
        """
        provider_lower = provider.lower().strip()

        if provider_lower == "openrouter":
            logger.info("OpenRouterクライアントを生成します")
            return OpenRouterClient(model=model)

        if provider_lower == "openai":
            logger.info("OpenAIクライアントを生成します")
            default_model = model or "gpt-4-turbo-preview"
            return OpenAIClient(api_key=api_key, model=default_model)

        if provider_lower == "gemini":
            logger.info("Geminiクライアントを生成します")
            default_model = model or "gemini-2.0-flash-exp"
            return GeminiClient(api_key=api_key, model=default_model)

        raise ValueError(
            f"未対応のLLMプロバイダーです: {provider}\n"
            "対応プロバイダー: 'openrouter', 'openai', 'gemini'"
        )

    @staticmethod
    def create_from_config(
        provider: str,
        openrouter_api_key: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        gemini_api_key: Optional[str] = None,
        model: Optional[str] = None,
    ) -> LLMClientInterface:
        """設定から LLMクライアントを生成

        Args:
            provider: プロバイダー名
            openrouter_api_key: OpenRouter APIキー
            openai_api_key: OpenAI APIキー
            gemini_api_key: Gemini APIキー
            model: モデル名（省略時はデフォルト）

        Returns:
            LLMClientInterface実装クラスのインスタンス

        Raises:
            ValueError: 必要なAPIキーが設定されていない場合
        """
        provider_lower = provider.lower().strip()

        if provider_lower == "openrouter":
            if not openrouter_api_key:
                raise ValueError("OPENROUTER_API_KEY が設定されていません")
            return LLMFactory.create_client("openrouter", openrouter_api_key, model)

        if provider_lower == "openai":
            if not openai_api_key:
                raise ValueError("OPENAI_API_KEY が設定されていません")
            return LLMFactory.create_client("openai", openai_api_key, model)

        if provider_lower == "gemini":
            if not gemini_api_key:
                raise ValueError("GEMINI_API_KEY が設定されていません")
            return LLMFactory.create_client("gemini", gemini_api_key, model)

        raise ValueError(
            f"未対応のLLMプロバイダーです: {provider}\n"
            "対応プロバイダー: 'openrouter', 'openai', 'gemini'"
        )
