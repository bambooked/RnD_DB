# 研究データ管理システム (Research Data Management System)

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Google Drive連携、AI研究相談、RAG検索を備えた統合研究データ管理システム

![Screenshot](docs/screenshot.png)

## ✨ 主要機能

### 🤖 AI研究相談
- **複数LLMプロバイダー対応**: OpenRouter、OpenAI、Geminiから選択可能
  - **OpenRouter**: Claude 3.5 Sonnet、GPT-4等、複数モデルを統一APIで利用
  - **OpenAI**: GPT-4 Turbo、GPT-4o等を直接利用
  - **Google Gemini**: Gemini 2.0等を直接利用
- **RAG検索**: セマンティック検索で関連文献を自動取得
- **7種類の相談タイプ**: 研究計画、方法論、データ分析等

### 📄 自動PDF解析
- **論文・ポスター自動解析**: タイトル、著者、アブストラクト、キーワード抽出
- **データセット解説生成**: CSV/JSON自動解析と概要作成
- **メタデータ管理**: SQLiteデータベースで効率的に管理

### ☁️ Google Drive連携
- **OAuth2認証**: Googleアカウントでシームレス認証
- **自動同期**: Drive上のファイルを自動インポート
- **ワンクリックアクセス**: UIから直接Google Driveへリンク

### 🔍 高度な検索
- **ベクトル検索**: セマンティック検索で意味ベースの検索
- **統合検索**: 論文・ポスター・データセットを横断検索
- **スマート推薦**: 関連性スコアに基づく精度の高い推薦

### 📊 データ管理
- **統計ダッシュボード**: 登録データの統計情報をリアルタイム表示
- **Looker Studioエクスポート**: データ可視化用CSV出力
- **重複防止**: コンテンツハッシュによる重複チェック

---

## 🚀 クイックスタート（3ステップ）

### 前提条件
- Docker & Docker Compose
- LLM APIキー（以下のいずれか）
  - [OpenRouter](https://openrouter.ai/) - 推奨（複数モデルを統一APIで利用）
  - [OpenAI](https://platform.openai.com/api-keys) - GPT-4等を直接利用
  - [Google AI Studio](https://makersuite.google.com/app/apikey) - Gemini利用

### 1. リポジトリのクローン
```bash
git clone https://github.com/yourusername/RnDDB.git
cd RnDDB/script
```

### 2. APIキー設定
```bash
cp .env.example .env
# .envファイルを編集してLLMプロバイダーとAPIキーを設定

# OpenRouterを使う場合（推奨）
echo "LLM_PROVIDER=openrouter" >> .env
echo "OPENROUTER_API_KEY=your_api_key_here" >> .env

# または OpenAI を使う場合
# echo "LLM_PROVIDER=openai" >> .env
# echo "OPENAI_API_KEY=your_api_key_here" >> .env

# または Gemini を使う場合
# echo "LLM_PROVIDER=gemini" >> .env
# echo "GEMINI_API_KEY=your_api_key_here" >> .env
```

### 3. 起動
```bash
docker-compose up
```

ブラウザで **http://localhost:8000** にアクセス

---

## 🛠 技術スタック

### バックエンド
- **Python 3.11+** - プログラミング言語
- **FastAPI** - 高性能WebAPIフレームワーク
- **SQLite / PostgreSQL** - データベース
- **ChromaDB** - ベクトルデータベース
- **sentence-transformers** - 埋め込みモデル

### AI/LLM
- **3つのLLMプロバイダー対応**:
  - **OpenRouter** - Claude、GPT-4、Gemini等を統一APIで利用（推奨）
  - **OpenAI** - GPT-4 Turbo、GPT-4o等を直接利用
  - **Google Gemini** - Gemini 2.0等を直接利用
- **柔軟なモデル選択** - 環境変数で簡単に切り替え可能

### フロントエンド
- **HTML5/CSS3/JavaScript**
- **TailwindCSS** - モダンUI
- **Chart.js** - データ可視化

### 外部サービス
- **Google Drive API** - クラウドストレージ連携
- **OAuth 2.0** - セキュア認証

---

## 📁 プロジェクト構造

```
RnDDB/script/
├── app/                        # メインアプリケーション
│   ├── main.py                 # FastAPIエントリーポイント
│   ├── core/                   # コア機能
│   ├── routers/                # APIルーティング
│   └── schemas/                # データスキーマ
├── agent/source/               # コアロジック
│   ├── database/               # データベース層
│   ├── analyzer/               # LLM解析
│   ├── advisor/                # AI研究相談
│   └── integrations/           # 外部サービス連携
├── services/                   # サービス層
│   ├── api/                    # HTTP API
│   └── rag_interface.py        # RAG統合
├── data/                       # 研究データ（gitignore）
│   ├── paper/                  # 論文PDF
│   ├── poster/                 # ポスターPDF
│   └── datasets/               # データセット
├── sample_data/                # デモ用サンプルデータ
├── templates/                  # HTMLテンプレート
├── static/                     # 静的ファイル
├── Dockerfile                  # Dockerイメージ定義
├── docker-compose.yml          # Docker Compose設定
└── README.md                   # このファイル
```

---

## 📖 使い方

### AI研究相談
1. ダッシュボードから「AI研究相談」をクリック
2. 相談タイプを選択（研究計画、方法論、データ分析等）
3. 質問を入力して送信
4. AIが関連文献を参照しながら回答

### データセット登録
```bash
# ローカルデータをdataディレクトリに配置
cp /path/to/papers/*.pdf data/paper/
cp /path/to/datasets/* data/datasets/

# UIから「データベース更新」をクリック
```

### Google Drive連携
1. UIから「Google Drive同期」をクリック
2. Googleアカウントで認証
3. 同期対象フォルダを選択
4. 「同期開始」をクリック

### ベクトル検索
```bash
# インデックス作成
curl -X POST http://localhost:8000/api/vector/index

# セマンティック検索
curl -X POST http://localhost:8000/api/vector/search \
  -H "Content-Type: application/json" \
  -d '{"query": "機械学習", "limit": 5}'
```

---

## 🔧 詳細セットアップ

### uvを使ったローカル開発
```bash
# 依存関係インストール
uv sync --dev

# .env設定
cp .env.example .env
# OPENROUTER_API_KEYを設定

# アプリケーション起動
uvicorn app.main:app --reload
```

### 環境変数設定
```env
# 必須
OPENROUTER_API_KEY=your_api_key_here

# オプション
OPENROUTER_MODEL=openrouter/anthropic/claude-3.5-sonnet
ENABLE_VECTOR_SEARCH=false
ENABLE_GOOGLE_DRIVE=false
DATABASE_PATH=agent/database/research_data.db
```

---

## 🧪 テスト

```bash
# 全テスト実行
uv run pytest agent/tests/ -v

# カバレッジ付き
uv run pytest agent/tests/ --cov=agent/source --cov-report=html

# コード品質チェック
uv run ruff check agent/
uv run mypy agent/
```

---

## 📊 サンプルデータ

このリポジトリには軽量版サンプルデータが含まれています：

- **論文**: 3件（1.2MB）
- **ポスター**: 2件（1.7MB）
- **データセット**: 6種類（18MB）
  - ESG企業レポート
  - バイアス研究データ
  - 環境排出量データ
  - その他

合計: 21MB

---

## 🚀 デプロイ

### Dockerでのデプロイ
```bash
# ビルド
docker-compose build

# 起動
docker-compose up -d

# ログ確認
docker-compose logs -f
```

### 本番環境（PostgreSQL）
```env
# .envに追加
DATABASE_URL=postgresql://user:pass@host:5432/dbname
ENABLE_VECTOR_SEARCH=true
AUTH_ENABLED=true
```

---

## 📝 API エンドポイント

### 基本エンドポイント
- `GET /` - ダッシュボード
- `GET /api/database/summary` - データベース統計
- `POST /api/search` - 研究データ検索
- `POST /api/consultation` - AI研究相談

### Google Drive連携
- `GET /api/auth/google/login` - Google認証開始
- `POST /api/sync/google-drive` - Drive同期実行
- `GET /api/drive/folders` - フォルダ一覧

### ベクトル検索
- `POST /api/vector/index` - インデックス作成
- `POST /api/vector/search` - セマンティック検索
- `GET /api/vector/status` - 検索エンジン状態

### データセット管理
- `GET /api/datasets` - データセット一覧
- `GET /api/datasets/{id}` - データセット詳細
- `GET /api/datasets/{id}/files` - データセット内ファイル

---

## 🐛 トラブルシューティング

### Dockerビルドエラー
```bash
# キャッシュクリア
docker-compose build --no-cache
```

### Google Drive認証エラー
1. OAuth 2.0クライアントIDの確認
2. リダイレクトURIの確認（`http://localhost:8000/api/auth/google/callback`）
3. Drive APIが有効化されているか確認

### ベクトル検索が動作しない
```bash
# .envで有効化
ENABLE_VECTOR_SEARCH=true

# インデックス再作成
curl -X POST http://localhost:8000/api/vector/index
```

---

## 🤝 貢献

プルリクエストやイシューの報告を歓迎します！

1. このリポジトリをフォーク
2. 機能ブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. プルリクエストを作成

---

## 📄 ライセンス

MIT License - 詳細は [LICENSE](LICENSE) を参照

---

## 🙏 謝辞

- [OpenRouter](https://openrouter.ai/) - LLM統合API
- [FastAPI](https://fastapi.tiangolo.com/) - Webフレームワーク
- [ChromaDB](https://www.trychroma.com/) - ベクトルデータベース
- [TailwindCSS](https://tailwindcss.com/) - CSSフレームワーク

---

## 📧 お問い合わせ

質問やフィードバックは [Issues](https://github.com/yourusername/RnDDB/issues) までお願いします。

---

**AI × RAGで研究データ管理を次のレベルへ！** 🚀
