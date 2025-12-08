"""LLM抽象化インターフェース

複数のLLMプロバイダー（OpenRouter、OpenAI、Gemini）を統一的に扱うための抽象基底クラス。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class LLMClientInterface(ABC):
    """LLMクライアントの抽象インターフェース"""

    @abstractmethod
    def generate_response(
        self,
        prompt: str,
        retry_count: int = 3,
        *,
        temperature: float = 0.7,
        top_p: float = 0.95,
        max_tokens: int = 1024,
    ) -> str:
        """汎用テキスト応答生成

        Args:
            prompt: プロンプト
            retry_count: リトライ回数
            temperature: 温度パラメータ
            top_p: Top-pパラメータ
            max_tokens: 最大トークン数

        Returns:
            生成されたテキスト

        Raises:
            RuntimeError: レスポンス取得に失敗した場合
        """
        pass

    @abstractmethod
    def analyze_text(
        self,
        text: str,
        prompt_template: str,
        retry_count: int = 3,
        **format_kwargs: Any,
    ) -> Optional[Dict[str, Any]]:
        """テキストを解析してJSONを取得

        Args:
            text: 解析対象のテキスト
            prompt_template: プロンプトテンプレート
            retry_count: リトライ回数
            **format_kwargs: テンプレートのフォーマット引数

        Returns:
            解析結果のJSON（辞書形式）、失敗時はNone
        """
        pass

    @abstractmethod
    def generate_research_advice_enhanced(
        self,
        prompt: str,
        retry_count: int = 3
    ) -> Optional[str]:
        """拡張研究アドバイス生成

        Args:
            prompt: プロンプト
            retry_count: リトライ回数

        Returns:
            研究アドバイステキスト、失敗時はNone
        """
        pass

    @abstractmethod
    def generate_dataset_description(
        self,
        dataset_name: str,
        file_list: List[Dict[str, Any]],
        retry_count: int = 3,
    ) -> Optional[str]:
        """データセット全体の解説を生成

        Args:
            dataset_name: データセット名
            file_list: ファイル情報のリスト
            retry_count: リトライ回数

        Returns:
            データセット解説テキスト、失敗時はNone
        """
        pass

    @abstractmethod
    def analyze_dataset_context(
        self,
        dataset_name: str,
        dataset_summary: str,
        user_question: str,
        retry_count: int = 3,
    ) -> Optional[str]:
        """データセットの文脈的解説生成

        Args:
            dataset_name: データセット名
            dataset_summary: データセット概要
            user_question: ユーザーの質問
            retry_count: リトライ回数

        Returns:
            文脈的解説テキスト、失敗時はNone
        """
        pass

    @abstractmethod
    def analyze_paper_metadata(
        self,
        file_name: str,
        content: str
    ) -> Optional[Dict[str, Any]]:
        """論文/ポスターのPDFからメタデータを抽出

        Args:
            file_name: ファイル名
            content: PDF内容のテキスト

        Returns:
            メタデータのJSON（辞書形式）、失敗時はNone
        """
        pass

    @abstractmethod
    def analyze_file_content(
        self,
        file_path: str,
        file_content: str,
        file_type: str,
    ) -> Optional[Dict[str, Any]]:
        """ファイル内容を解析

        Args:
            file_path: ファイルパス
            file_content: ファイル内容
            file_type: ファイルタイプ（pdf, csv, json, jsonl等）

        Returns:
            解析結果のJSON（辞書形式）、失敗時はNone
        """
        pass

    @abstractmethod
    def analyze_dataset_collection(
        self,
        dataset_name: str,
        file_contents: List[Dict[str, str]],
    ) -> Optional[Dict[str, Any]]:
        """データセット全体（複数ファイル）を解析

        Args:
            dataset_name: データセット名
            file_contents: ファイル情報のリスト（name, contentを含む辞書）

        Returns:
            解析結果のJSON（辞書形式）、失敗時はNone
        """
        pass

    @abstractmethod
    def generate_research_advice(
        self,
        query: str,
        relevant_documents: List[Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        """研究アドバイスを生成

        Args:
            query: ユーザーの研究相談
            relevant_documents: 関連文書のリスト

        Returns:
            アドバイスのJSON（辞書形式）、失敗時はNone
        """
        pass
