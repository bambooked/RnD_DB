import json
from typing import Dict, Any, Optional, List
import logging
import time

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from tools.config import GEMINI_API_KEY, GEMINI_MODEL

logger = logging.getLogger(__name__)


class GeminiClient:
    """Google Gemini APIクライアント"""
    
    def __init__(self):
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY が設定されていません")
        
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel(
            model_name=GEMINI_MODEL,
            generation_config={
                "temperature": 0.7,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 8192,
                "response_mime_type": "application/json",
            },
            safety_settings={
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            }
        )
        
        logger.info(f"Gemini クライアント初期化完了: モデル={GEMINI_MODEL}")
    
    def generate_research_advice_enhanced(self, prompt: str, retry_count: int = 3) -> Optional[str]:
        """拡張研究アドバイス生成"""
        for attempt in range(retry_count):
            try:
                # 研究アドバイス用のモデル設定（JSONではなくテキスト出力）
                advice_model = genai.GenerativeModel(
                    model_name=GEMINI_MODEL,
                    generation_config={
                        "temperature": 0.8,
                        "top_p": 0.95,
                        "top_k": 40,
                        "max_output_tokens": 4096,
                        "response_mime_type": "text/plain",
                    },
                    safety_settings={
                        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                    }
                )
                
                response = advice_model.generate_content(prompt)
                
                if response.text:
                    logger.info("拡張研究アドバイス生成成功")
                    return response.text.strip()
                else:
                    logger.warning(f"空のレスポンス (試行 {attempt + 1}/{retry_count})")
                    
            except Exception as e:
                logger.error(f"拡張研究アドバイス生成エラー (試行 {attempt + 1}/{retry_count}): {e}")
                if attempt < retry_count - 1:
                    time.sleep(2 ** attempt)
                else:
                    logger.error("拡張研究アドバイス生成失敗: 最大試行回数に到達")
        
        return None
    
    def generate_dataset_description(self, dataset_name: str, file_list: List[Dict[str, Any]],
                                    retry_count: int = 3) -> Optional[str]:
        """データセット全体の解説を生成"""
        # ファイル情報をまとめる
        file_info_text = []
        for f in file_list[:10]:  # 最初の10ファイルのみ
            file_info_text.append(f"- {f.get('name', 'unknown')} ({f.get('type', 'unknown')}, {f.get('size', 0) / 1024:.1f} KB)")

        prompt = f"""以下のデータセットについて、300文字程度で詳細な解説を生成してください。

データセット名: {dataset_name}
ファイル数: {len(file_list)}
ファイル一覧（一部）:
{chr(10).join(file_info_text)}

以下の観点で解説してください:
1. データセットの目的・用途
2. 含まれるデータの種類と特徴
3. 想定される利用シーン（研究分野、分析手法など）
4. データセットの特徴的な点

「このデータセットは」で始まる自然な文章で記述してください。
"""

        for attempt in range(retry_count):
            try:
                # テキスト形式で生成
                model = genai.GenerativeModel(
                    model_name=GEMINI_MODEL,
                    generation_config={
                        "temperature": 0.7,
                        "top_p": 0.95,
                        "max_output_tokens": 1024,
                        "response_mime_type": "text/plain",
                    }
                )

                response = model.generate_content(prompt)

                if response.text:
                    description = response.text.strip()
                    logger.info(f"データセット解説生成成功: {dataset_name}")
                    return description

            except Exception as e:
                logger.error(f"データセット解説生成エラー (試行 {attempt + 1}/{retry_count}): {e}")
                if attempt < retry_count - 1:
                    time.sleep(2 ** attempt)

        return None

    def analyze_dataset_context(self, dataset_name: str, dataset_summary: str,
                              user_question: str, retry_count: int = 3) -> Optional[str]:
        """データセットの文脈的解説生成"""
        prompt = f"""あなたはデータサイエンス・研究支援の専門家です。
以下のデータセットについて、ユーザーの質問に答えてください。

【データセット名】
{dataset_name}

【データセット概要】
{dataset_summary}

【ユーザーの質問】
{user_question}

以下の観点で詳細な解説を提供してください：
1. データセットの特徴と構造
2. 研究・分析での活用可能性
3. 推奨される分析手法
4. 注意すべき点やデータの制限
5. 類似研究での活用事例

実践的で具体的な回答を心がけてください。"""

        for attempt in range(retry_count):
            try:
                advice_model = genai.GenerativeModel(
                    model_name=GEMINI_MODEL,
                    generation_config={
                        "temperature": 0.7,
                        "top_p": 0.95,
                        "max_output_tokens": 3072,
                        "response_mime_type": "text/plain",
                    }
                )
                
                response = advice_model.generate_content(prompt)
                
                if response.text:
                    logger.info(f"データセット解説生成成功: {dataset_name}")
                    return response.text.strip()
                    
            except Exception as e:
                logger.error(f"データセット解説生成エラー (試行 {attempt + 1}/{retry_count}): {e}")
                if attempt < retry_count - 1:
                    time.sleep(2 ** attempt)
        
        return None
    
    def analyze_text(self, text: str, prompt_template: str,
                    retry_count: int = 3) -> Optional[Dict[str, Any]]:
        """テキストを解析"""
        prompt = prompt_template.format(text=text)

        for attempt in range(retry_count):
            try:
                response = self.model.generate_content(prompt)

                if response.text:
                    # JSON形式で返されることを期待
                    try:
                        # レスポンステキストをクリーンアップ（マークダウンのコードブロックを除去）
                        response_text = response.text.strip()

                        # マークダウンコードブロックの除去
                        if response_text.startswith('```json'):
                            response_text = response_text[7:]
                        elif response_text.startswith('```'):
                            response_text = response_text[3:]

                        if response_text.endswith('```'):
                            response_text = response_text[:-3]

                        response_text = response_text.strip()

                        # 改行を正規化（\r\nを\nに統一）
                        response_text = response_text.replace('\r\n', '\n')

                        # JSONパース試行
                        result = json.loads(response_text)
                        return result

                    except json.JSONDecodeError as e:
                        logger.warning(f"JSONパースエラー (試行 {attempt + 1}/{retry_count}): {e}")
                        logger.error(f"問題のレスポンス: {response.text[:500]}")

                        # 最後の試行でない場合はリトライ
                        if attempt < retry_count - 1:
                            logger.info("リトライします...")
                            time.sleep(2 ** attempt)
                            continue

                        # 最後の試行でも失敗した場合はNoneを返す
                        logger.error("最大試行回数に達しました。JSONパースに失敗しました。")
                        return None
                else:
                    logger.warning("空のレスポンスが返されました")
                    
            except Exception as e:
                logger.error(f"Gemini API エラー (試行 {attempt + 1}/{retry_count}): {e}")
                if attempt < retry_count - 1:
                    time.sleep(2 ** attempt)  # エクスポネンシャルバックオフ
                else:
                    raise
        
        return None
    
    def analyze_file_content(self, file_path: str, file_content: str, 
                           file_type: str) -> Optional[Dict[str, Any]]:
        """ファイル内容を解析"""
        if file_type == "pdf":
            return self._analyze_pdf_content(file_content)
        elif file_type in ["csv", "json", "jsonl"]:
            return self._analyze_data_content(file_content, file_type)
        else:
            logger.warning(f"未対応のファイルタイプ: {file_type}")
            return None
    
    def analyze_paper_metadata(self, file_name: str, content: str) -> Optional[Dict[str, Any]]:
        """論文/ポスターのPDFからメタデータ（タイトル、著者、要約など）を抽出"""
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
        # analyze_textを使わず直接APIを呼び出す
        for attempt in range(3):
            try:
                response = self.model.generate_content(prompt)

                if response.text:
                    try:
                        # レスポンステキストをクリーンアップ
                        response_text = response.text.strip()

                        # マークダウンコードブロックの除去
                        if response_text.startswith('```json'):
                            response_text = response_text[7:]
                        elif response_text.startswith('```'):
                            response_text = response_text[3:]

                        if response_text.endswith('```'):
                            response_text = response_text[:-3]

                        response_text = response_text.strip()

                        # JSONパース
                        result = json.loads(response_text)
                        logger.info(f"論文メタデータ解析成功: {file_name}")
                        return result

                    except json.JSONDecodeError as e:
                        logger.warning(f"JSONパースエラー (試行 {attempt + 1}/3): {e}")
                        if attempt < 2:
                            time.sleep(2 ** attempt)
                            continue
                        logger.error(f"レスポンス内容: {response.text[:500]}")
                        return None

            except Exception as e:
                logger.error(f"論文メタデータ解析エラー (試行 {attempt + 1}/3): {e}")
                if attempt < 2:
                    time.sleep(2 ** attempt)

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
        prompt = prompt_template.format(text=content[:3000], file_type=file_type)
        return self.analyze_text(content, prompt)
    
    def analyze_dataset_collection(self, dataset_name: str, 
                                 file_contents: List[Dict[str, str]]) -> Optional[Dict[str, Any]]:
        """データセット全体（複数ファイル）を解析"""
        # ファイル内容をまとめる
        combined_content = f"データセット名: {dataset_name}\n\n"
        for i, file_info in enumerate(file_contents, 1):
            combined_content += f"ファイル{i}: {file_info['name']}\n"
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
    
    def generate_research_advice(self, query: str, 
                               relevant_documents: list) -> Optional[Dict[str, Any]]:
        """研究アドバイスを生成"""
        docs_summary = "\n\n".join([
            f"文書{i+1}: {doc.get('title', 'タイトルなし')}\n"
            f"要約: {doc.get('summary', '要約なし')}\n"
            f"キーワード: {', '.join(doc.get('keywords', []))}"
            for i, doc in enumerate(relevant_documents[:5])
        ])
        
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
        prompt = prompt_template.format(query=query, docs_summary=docs_summary)
        return self.analyze_text("", prompt)