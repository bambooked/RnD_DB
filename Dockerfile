FROM python:3.11-slim

WORKDIR /app

# システム依存関係のインストール
RUN apt-get update && apt-get install -y \
    sqlite3 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# uvのインストール
RUN pip install --no-cache-dir uv

# pyproject.tomlをコピーして依存関係をインストール
COPY pyproject.toml ./
RUN uv pip install --system -e .

# アプリケーションコードをコピー
COPY . .

# データベースとデータディレクトリの作成
RUN mkdir -p agent/database data/paper data/poster data/datasets

# ポート公開
EXPOSE 8000

# ヘルスチェック
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# アプリケーション起動
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
