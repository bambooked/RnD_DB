import os
from pathlib import Path
from typing import List
from dotenv import load_dotenv

# .envファイルから環境変数を読み込む
load_dotenv()

# 基本パス
BASE_DIR = Path(__file__).parent.parent  # プロジェクトルートに移動
DATA_DIR = BASE_DIR / os.getenv("DATA_DIR_PATH", "data")
DATABASE_DIR = BASE_DIR / "agent" / "database"

# LLMプロバイダー設定
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openrouter").lower()

# OpenRouter API設定
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")
OPENROUTER_API_BASE = os.getenv("OPENROUTER_API_BASE", "https://openrouter.ai/api/v1")
OPENROUTER_REFERER = os.getenv("OPENROUTER_REFERER")
OPENROUTER_TITLE = os.getenv("OPENROUTER_TITLE")

# OpenAI API設定
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")

# Google Gemini API設定
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")

# データベース設定
DATABASE_PATH = Path(os.getenv("DATABASE_PATH", str(DATABASE_DIR / "research_data.db")))

# アプリケーション設定
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "100"))
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

# サポートするファイル拡張子
SUPPORTED_EXTENSIONS_STR = os.getenv("SUPPORTED_EXTENSIONS", "pdf,csv,json,jsonl")
SUPPORTED_EXTENSIONS: List[str] = [
    f".{ext.strip()}" for ext in SUPPORTED_EXTENSIONS_STR.split(",")
]

# ログ設定
import logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# pypdf関連の警告を完全に抑制
logging.getLogger('pypdf').setLevel(logging.CRITICAL)
logging.getLogger('pypdf._cmap').setLevel(logging.CRITICAL)
logging.getLogger('pypdf._reader').setLevel(logging.CRITICAL)

def validate_config():
    """設定の妥当性を検証"""
    errors = []

    # LLMプロバイダーに応じたAPIキー確認
    if LLM_PROVIDER == "openrouter":
        if not OPENROUTER_API_KEY:
            errors.append("LLM_PROVIDER=openrouter ですが、OPENROUTER_API_KEY が設定されていません")
    elif LLM_PROVIDER == "openai":
        if not OPENAI_API_KEY:
            errors.append("LLM_PROVIDER=openai ですが、OPENAI_API_KEY が設定されていません")
    elif LLM_PROVIDER == "gemini":
        if not GEMINI_API_KEY:
            errors.append("LLM_PROVIDER=gemini ですが、GEMINI_API_KEY が設定されていません")
    else:
        errors.append(f"未対応のLLMプロバイダーです: {LLM_PROVIDER}（openrouter, openai, gemini のいずれかを指定してください）")

    if not DATA_DIR.exists():
        errors.append(f"データディレクトリが存在しません: {DATA_DIR}")

    # データベースディレクトリが存在しない場合は作成
    DATABASE_DIR.mkdir(parents=True, exist_ok=True)

    if errors:
        for error in errors:
            logging.error(error)
        raise ValueError("設定エラーがあります。.envファイルを確認してください。")

    logging.info("設定の検証が完了しました（LLMプロバイダー: %s）", LLM_PROVIDER)

# カテゴリーマッピング
CATEGORY_MAPPING = {
    "paper": "論文",
    "poster": "ポスター", 
    "datasets": "データセット"
}
