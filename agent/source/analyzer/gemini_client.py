"""Google Gemini APIクライアント実装

Google Gemini 2.0等のモデルを利用するためのクライアント実装。
"""

import json
import logging
import time
from typing import Any, Dict, List, Optional

import requests

from agent.source.analyzer.llm_interface import LLMClientInterface
from services.admin_metrics import admin_metrics

logger = logging.getLogger(__name__)


class GeminiClient(LLMClientInterface):
    """Google Gemini API クライアント"""

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash-exp"):
        if not api_key:
            raise ValueError("Gemini API Key が設定されていません")

        self.api_key = api_key
        self.model = model
        self.session = requests.Session()
        # Gemini APIのエンドポイント
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"

        logger.info("Gemini クライアント初期化完了: モデル=%s", self.model)

    def _make_request(
        self,
        prompt: str,
        *,
        temperature: float = 0.7,
        top_p: float = 0.95,
        max_tokens: Optional[int] = None,
        retry_count: int = 3,
    ) -> Optional[str]:
        """Gemini APIリクエスト実行"""
        last_error: Optional[Exception] = None

        # エンドポイント構築
        endpoint = f"{self.base_url}/{self.model}:generateContent?key={self.api_key}"

        for attempt in range(retry_count):
            payload: Dict[str, Any] = {
                "contents": [{
                    "parts": [{"text": prompt}]
                }],
                "generationConfig": {
                    "temperature": temperature,
                    "topP": top_p,
                }
            }
            if max_tokens is not None:
                payload["generationConfig"]["maxOutputTokens"] = max_tokens

            try:
                response = self.session.post(
                    endpoint,
                    headers={"Content-Type": "application/json"},
                    json=payload,
                    timeout=90,
                )
                response.raise_for_status()
                data = response.json()

                # レスポンスからテキスト抽出
                text = self._extract_text(data)
                if text:
                    # 使用量記録（Geminiの場合は概算）
                    try:
                        estimated_prompt_tokens = len(prompt.split()) * 1.3  # 概算
                        estimated_completion_tokens = len(text.split()) * 1.3  # 概算
                        admin_metrics.record_llm_usage(
                            model=self.model,
                            prompt_tokens=int(estimated_prompt_tokens),
                            completion_tokens=int(estimated_completion_tokens),
                            total_tokens=int(estimated_prompt_tokens + estimated_completion_tokens),
                        )
                    except Exception as metrics_error:  # pylint: disable=broad-except
                        logger.warning("LLM使用量記録に失敗: %s", metrics_error)

                    return text.strip()

                logger.warning("Gemini API: 空のレスポンスが返されました")

            except requests.RequestException as exc:
                last_error = exc
                logger.error(
                    "Gemini API リクエストエラー (試行 %s/%s): %s",
                    attempt + 1,
                    retry_count,
                    exc,
                )
            except ValueError as exc:
                last_error = exc
                logger.error(
                    "Gemini API レスポンス解析エラー (試行 %s/%s): %s",
                    attempt + 1,
                    retry_count,
                    exc,
                )

            if attempt < retry_count - 1:
                time.sleep(2 ** attempt)

        if last_error:
            raise last_error
        return None

    @staticmethod
    def _extract_text(data: Dict[str, Any]) -> Optional[str]:
        """Gemini APIレスポンスからテキストを抽出"""
        try:
            candidates = data.get("candidates", [])
            if not candidates:
                return None

            content = candidates[0].get("content", {})
            parts = content.get("parts", [])
            if not parts:
                return None

            text = parts[0].get("text", "")
            return text if text else None

        except (KeyError, IndexError, TypeError) as exc:
            logger.error("レスポンス解析エラー: %s", exc)
            return None

    def generate_response(
        self,
        prompt: str,
        retry_count: int = 3,
        *,
        temperature: float = 0.7,
        top_p: float = 0.95,
        max_tokens: int = 1024,
    ) -> str:
        """汎用テキスト応答生成"""
        text = self._make_request(
            prompt,
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
            retry_count=retry_count,
        )
        if not text:
            raise RuntimeError("Gemini APIから有効なレスポンスが得られませんでした")
        return text

    def analyze_text(
        self,
        text: str,
        prompt_template: str,
        retry_count: int = 3,
        **format_kwargs: Any,
    ) -> Optional[Dict[str, Any]]:
        """テキストを解析してJSONを取得"""
        format_values: Dict[str, Any] = {"text": text}
        format_values.update(format_kwargs)

        try:
            prompt = prompt_template.format(**format_values)
        except KeyError:
            prompt = prompt_template

        # JSON形式を強制するためのプロンプト追加
        prompt += "\n\n必ず有効なJSON形式で返してください。"

        try:
            response_text = self._make_request(
                prompt,
                temperature=0.7,
                top_p=0.95,
                max_tokens=8192,
                retry_count=retry_count,
            )
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("テキスト解析エラー: %s", exc)
            return None

        if not response_text:
            logger.warning("空のレスポンスが返されました")
            return None

        # JSONパース
        cleaned = response_text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip().replace("\r\n", "\n")

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as exc:
            logger.error("JSONパースエラー: %s", exc)
            logger.debug("レスポンス内容: %s", cleaned[:500])
            return None

    def generate_research_advice_enhanced(self, prompt: str, retry_count: int = 3) -> Optional[str]:
        """拡張研究アドバイス生成"""
        try:
            text = self._make_request(
                prompt,
                temperature=0.8,
                top_p=0.95,
                max_tokens=4096,
                retry_count=retry_count,
            )
            if text:
                logger.info("拡張研究アドバイス生成成功")
                return text
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("拡張研究アドバイス生成エラー: %s", exc)
        return None

    def generate_dataset_description(
        self,
        dataset_name: str,
        file_list: List[Dict[str, Any]],
        retry_count: int = 3,
    ) -> Optional[str]:
        """データセット全体の解説を生成"""
        file_info_text = []
        for file_info in file_list[:10]:
            size_kb = file_info.get("size", 0) / 1024 if file_info.get("size") else 0
            file_info_text.append(
                f"- {file_info.get('name', 'unknown')} "
                f"({file_info.get('type', 'unknown')}, {size_kb:.1f} KB)"
            )

        prompt = (
            "以下のデータセットについて、300文字程度で詳細な解説を生成してください。\n\n"
            f"データセット名: {dataset_name}\n"
            f"ファイル数: {len(file_list)}\n"
            "ファイル一覧（一部）:\n"
            f"{chr(10).join(file_info_text)}\n\n"
            "以下の観点で解説してください:\n"
            "1. データセットの目的・用途\n"
            "2. 含まれるデータの種類と特徴\n"
            "3. 想定される利用シーン（研究分野、分析手法など）\n"
            "4. データセットの特徴的な点\n\n"
            "「このデータセットは」で始まる自然な文章で記述してください。"
        )

        try:
            text = self._make_request(
                prompt,
                temperature=0.7,
                top_p=0.95,
                max_tokens=1024,
                retry_count=retry_count,
            )
            if text:
                logger.info("データセット解説生成成功: %s", dataset_name)
                return text
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("データセット解説生成エラー: %s", exc)
        return None

    def analyze_dataset_context(
        self,
        dataset_name: str,
        dataset_summary: str,
        user_question: str,
        retry_count: int = 3,
    ) -> Optional[str]:
        """データセットの文脈的解説生成"""
        prompt = (
            "あなたはデータサイエンス・研究支援の専門家です。\n"
            "以下のデータセットについて、ユーザーの質問に答えてください。\n\n"
            "【データセット名】\n"
            f"{dataset_name}\n\n"
            "【データセット概要】\n"
            f"{dataset_summary}\n\n"
            "【ユーザーの質問】\n"
            f"{user_question}\n\n"
            "以下の観点で詳細な解説を提供してください：\n"
            "1. データセットの特徴と構造\n"
            "2. 研究・分析での活用可能性\n"
            "3. 推奨される分析手法\n"
            "4. 注意すべき点やデータの制限\n"
            "5. 類似研究での活用事例\n\n"
            "実践的で具体的な回答を心がけてください。"
        )

        try:
            text = self._make_request(
                prompt,
                temperature=0.7,
                top_p=0.95,
                max_tokens=3072,
                retry_count=retry_count,
            )
            if text:
                logger.info("データセット文脈解説生成成功: %s", dataset_name)
                return text
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("データセット文脈解説生成エラー: %s", exc)
        return None

    def analyze_paper_metadata(self, file_name: str, content: str) -> Optional[Dict[str, Any]]:
        """論文/ポスターのPDFからメタデータを抽出"""
        prompt = f"""以下の研究論文またはポスターのPDFテキストから、メタデータを抽出してJSON形式で返してください。

ファイル名: {file_name}

PDF内容（最初の部分）:
{content[:10000]}

必ず以下のJSON形式のみを返してください（説明文などは不要です）:
{{
    "title": "論文/ポスターのタイトル（PDFから抽出、なければファイル名から推測）",
    "authors": "著者名（複数いればカンマ区切り）",
    "abstract": "要約・アブストラクト（200文字以内、なければPDFの最初の部分から作成）",
    "keywords": "キーワード（カンマ区切り）",
    "year": "発表年（もし記載があれば、なければ空文字）",
    "conference_or_journal": "学会名または雑誌名（もし記載があれば、なければ空文字）",
    "cited_datasets": ["引用されているデータセット名1", "引用されているデータセット名2"],
    "research_field": "研究分野"
}}

重要:
- 必ず有効なJSONのみを返してください
- titleは論文の正式なタイトルを抽出してください
- authorsは著者全員を記載してください
- cited_datasetsには本文中で言及されているデータセット名を全て含めてください（なければ空配列）
- すべてのフィールドは必須です（値がなければ空文字または空配列を使用）
"""

        result = self.analyze_text(
            content,
            prompt,
            retry_count=3,
        )
        if result is not None:
            logger.info("論文メタデータ解析成功: %s", file_name)
        return result

    def analyze_file_content(
        self,
        file_path: str,
        file_content: str,
        file_type: str,
    ) -> Optional[Dict[str, Any]]:
        """ファイル内容を解析"""
        if file_type == "pdf":
            return self._analyze_pdf_content(file_content)
        if file_type in ["csv", "json", "jsonl"]:
            return self._analyze_data_content(file_content, file_type)

        logger.warning("未対応のファイルタイプ: %s", file_type)
        return None

    def _analyze_pdf_content(self, content: str) -> Optional[Dict[str, Any]]:
        """PDF文書を解析"""
        prompt_template = """
以下の文書を分析し、JSON形式で結果を返してください。

文書内容:
{text}

以下の形式で返してください:
{{
    "summary": "文書の要約（200文字以内）",
    "main_topics": ["主要なトピック1", "主要なトピック2", ...],
    "keywords": ["キーワード1", "キーワード2", ...],
    "language": "主要言語（japanese/english）",
    "document_type": "文書タイプ（paper/poster/report/other）",
    "research_field": "研究分野",
    "key_findings": ["主要な発見1", "主要な発見2", ...]
}}
"""
        return self.analyze_text(content, prompt_template)

    def _analyze_data_content(self, content: str, file_type: str) -> Optional[Dict[str, Any]]:
        """データファイルを解析"""
        prompt_template = """
以下のデータファイル（{file_type}形式）を分析し、JSON形式で結果を返してください。

データ内容（最初の部分）:
{text}

以下の形式で返してください:
{{
    "summary": "このデータセットは[データの内容・目的・特徴を説明]。（200文字以内）",
    "data_structure": "データ構造の説明",
    "columns": ["カラム名1", "カラム名2", ...],
    "row_count": "推定行数",
    "data_types": {{"カラム名": "データ型", ...}},
    "potential_use_cases": ["使用事例1", "使用事例2", ...],
    "data_quality_notes": "データ品質に関する注記"
}}

重要: summaryは必ず「このデータセットは」で始めてください。
"""
        return self.analyze_text(
            content,
            prompt_template,
            file_type=file_type,
            text=content[:3000],
        )

    def analyze_dataset_collection(
        self,
        dataset_name: str,
        file_contents: List[Dict[str, str]],
    ) -> Optional[Dict[str, Any]]:
        """データセット全体（複数ファイル）を解析"""
        combined_content = f"データセット名: {dataset_name}\n\n"
        for index, file_info in enumerate(file_contents, 1):
            combined_content += f"ファイル{index}: {file_info['name']}\n"
            combined_content += f"内容: {file_info['content'][:1000]}\n\n"

        prompt_template = """
以下のデータセット全体を分析し、JSON形式で結果を返してください。

{text}

以下の形式で返してください:
{{
    "summary": "このデータセットは[データセット全体の内容・目的・特徴を総合的に説明]。（300文字以内）",
    "main_purpose": "データセットの主な目的",
    "data_types": ["データタイプ1", "データタイプ2", ...],
    "research_domains": ["研究領域1", "研究領域2", ...],
    "key_features": ["特徴1", "特徴2", ...],
    "potential_applications": ["応用例1", "応用例2", ...],
    "file_descriptions": {{"ファイル名": "説明", ...}}
}}

重要: summaryは必ず「このデータセットは」で始めてください。
"""
        return self.analyze_text(combined_content, prompt_template)

    def generate_research_advice(
        self,
        query: str,
        relevant_documents: List[Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        """研究アドバイスを生成"""
        docs_summary = "\n\n".join(
            [
                f"文書{i + 1}: {doc.get('title', 'タイトルなし')}\n"
                f"要約: {doc.get('summary', '要約なし')}\n"
                f"キーワード: {', '.join(doc.get('keywords', []))}"
                for i, doc in enumerate(relevant_documents[:5])
            ]
        )

        prompt_template = """
ユーザーの研究相談:
{query}

関連する文書:
{docs_summary}

以下の形式でアドバイスを提供してください:
{{
    "advice": "研究アドバイス（500文字以内）",
    "recommended_approaches": ["推奨アプローチ1", "推奨アプローチ2", ...],
    "relevant_keywords": ["関連キーワード1", "関連キーワード2", ...],
    "next_steps": ["次のステップ1", "次のステップ2", ...],
    "potential_challenges": ["潜在的な課題1", "潜在的な課題2", ...]
}}
"""
        return self.analyze_text(
            "",
            prompt_template,
            query=query,
            docs_summary=docs_summary,
        )
