# 研究データ管理システム - R&D DB

<div align="center">
  <img src="docs/images/icon.png" alt="R&D DB Icon" width="200"/>
</div>

<div align="center">
  <strong>Google Drive連携 & AI研究相談を備えた研究データ管理システム</strong>
</div>

---

## 📖 なぜこのシステムを作ったのか

研究活動において、論文、データセット、ポスターなどの研究成果物は日々増え続けます。しかし、これらのデータは散在しがちで、以下のような課題がありました：

- **データの所在が分からない**: 「あのデータセット、どこに保存したっけ？」
- **関連性の把握が困難**: 「この論文に使われているデータセットはどれ？」
- **検索の非効率性**: ファイル名だけでは内容を理解できない
- **研究相談の不在**: 深夜や休日に研究の方向性を相談できる相手がいない

このシステムは、これらの課題を**Google Drive連携**と**AI技術（RAG + LLM）**で解決し、研究者が本来の研究に集中できる環境を提供します。

---

## 🎯 システム概要

このシステムは3つの核心機能で研究活動を支援します：

### 1. Google Drive連携による自動データ管理
Google Driveに保存された研究データを自動的に同期・解析し、メタデータを抽出してデータベースに格納します。

### 2. セマンティック検索（ベクトル検索）
キーワードだけでなく、意味的な関連性に基づいて論文やデータセットを検索できます。

### 3. AI研究相談（RAG + LLM）
データベース内の研究データをコンテキストとして、LLMが的確な研究アドバイスを提供します。

---

## 🖼️ 動作イメージ

### ダッシュボード
<div align="center">
  <img src="docs/images/dashboad_sample.png" alt="Dashboard" width="800"/>
</div>

システム全体の統計情報とデータベースの状態をリアルタイムで確認できます。

### AI研究相談
<div align="center">
  <img src="docs/images/chat_sample.png" alt="Chat Interface" width="800"/>
</div>

研究に関する質問をすると、データベース内の関連データを参照しながらAIが回答します。

---

## 🛠️ 技術スタック

### バックエンド

| 技術 | バージョン | 選定理由 |
|------|-----------|---------|
| **Python** | 3.11+ | 豊富なデータ処理・ML/AIライブラリ |
| **FastAPI** | - | 高速な非同期処理、自動APIドキュメント生成 |
| **SQLite** | - | 開発環境での軽量なデータ永続化 |
| **PostgreSQL** | - | 本番環境でのスケーラブルなDB |
| **ChromaDB** | - | ベクトル検索のためのローカルDB |
| **sentence-transformers** | all-MiniLM-L6-v2 | 軽量かつ高精度な埋め込みモデル |

### LLM API統合

| サービス | 用途 |
|---------|------|
| **OpenRouter API** | Claude, GPT-4等の複数LLMへの統一アクセス |
| **Google Gemini API** | 論文・データセット解析（レガシー実装） |

### フロントエンド

| 技術 | 用途 |
|------|------|
| **TailwindCSS** | モダンでレスポンシブなUI構築 |
| **Jinja2** | サーバーサイドテンプレート |
| **Chart.js** | データ可視化 |

### 外部サービス連携

| サービス | 用途 |
|---------|------|
| **Google Drive API** | クラウドストレージ連携・自動同期 |
| **OAuth 2.0** | セキュアなユーザー認証 |

---

## 📁 アーキテクチャとディレクトリ構造

### システムアーキテクチャ

```
┌─────────────┐
│   Web UI    │ (FastAPI + Jinja2)
└──────┬──────┘
       │
┌──────▼──────────────────────────────────┐
│        Core Application Layer            │
│  ┌──────────┐  ┌──────────┐  ┌────────┐ │
│  │ Indexer  │  │ Analyzer │  │ Advisor│ │
│  └──────────┘  └──────────┘  └────────┘ │
└──────┬──────────────┬───────────────────┘
       │              │
┌──────▼──────┐  ┌───▼──────────┐
│   Database  │  │ Vector Store │
│  (SQLite/   │  │  (ChromaDB)  │
│ PostgreSQL) │  │              │
└─────────────┘  └──────────────┘
       │
┌──────▼──────────────┐
│  External Services  │
│ ┌─────────────────┐ │
│ │ Google Drive    │ │
│ │ OpenRouter API  │ │
│ └─────────────────┘ │
└─────────────────────┘
```

### ディレクトリ構造

```
/
├── app/                          # メインアプリケーション
│   ├── main.py                   # FastAPIエントリーポイント
│   ├── core/
│   │   └── context.py            # シングルトンコンテキスト管理
│   ├── routers/
│   │   └── pages.py              # ページルーティング
│   └── schemas/
│       └── api.py                # APIスキーマ定義
│
├── agent/source/                 # コアビジネスロジック
│   ├── database/                 # データベース層
│   │   ├── connection.py         # DB接続管理
│   │   ├── new_models.py         # データモデル
│   │   └── new_repository.py     # リポジトリパターン実装
│   │
│   ├── indexer/                  # ファイルインデクサー
│   │   ├── new_indexer.py        # ファイルスキャン・登録
│   │   └── scanner.py            # ファイルシステムスキャナー
│   │
│   ├── analyzer/                 # AI解析エンジン
│   │   ├── new_analyzer.py       # メタデータ抽出
│   │   ├── gemini_client.py      # Gemini APIクライアント
│   │   └── openrouter_client.py  # OpenRouter APIクライアント
│   │
│   ├── advisor/                  # AI研究相談
│   │   ├── dataset_advisor.py    # データセット推薦
│   │   └── enhanced_research_advisor.py  # RAG統合アドバイザー
│   │
│   ├── integrations/             # 外部サービス統合
│   │   ├── google_drive.py       # Google Drive連携
│   │   ├── vector_search.py      # ベクトル検索
│   │   ├── vector_indexer.py     # ベクトルインデックス管理
│   │   ├── auth.py               # 認証管理
│   │   └── looker_export.py      # データエクスポート
│   │
│   └── interfaces/               # 抽象化レイヤー（並行開発用）
│       ├── data_models.py        # 共通データ型
│       ├── auth_ports.py         # 認証インターフェース
│       └── fastapi_auth_middleware.py  # 認証ミドルウェア
│
├── services/                     # サービス層
│   ├── rag_interface.py          # RAG統合インターフェース
│   ├── admin_metrics.py          # 管理者メトリクス
│   └── api/                      # HTTP APIサーバー
│       ├── paas_api.py           # 開発用API（認証なし）
│       └── paas_api_with_auth.py # 本番用API（認証あり）
│
├── templates/                    # HTMLテンプレート
│   ├── base.html
│   ├── dashboard.html
│   ├── chat.html
│   ├── search.html
│   └── drive_sync.html
│
├── static/                       # 静的ファイル（CSS/JS/画像）
├── data/                         # 研究データ
│   ├── datasets/                 # データセット（CSV/JSON/JSONL）
│   ├── paper/                    # 論文PDF
│   └── poster/                   # ポスターPDF
│
├── chroma_db/                    # ベクトルDB永続化
├── credentials/                  # 認証情報（.gitignore）
├── docs/                         # ドキュメント
├── scripts/                      # ユーティリティスクリプト
└── tools/
    └── config.py                 # 設定ファイル
```

### 設計の特徴

#### 1. レイヤードアーキテクチャ
- **プレゼンテーション層**: FastAPI + Jinja2によるWebUI
- **ビジネスロジック層**: agent/source/内のコアモジュール
- **データアクセス層**: リポジトリパターンによるDB抽象化

#### 2. シングルトンコンテキスト管理
`app/core/context.py`で全コンポーネントを一元管理し、依存性注入を実現。

#### 3. ポート&アダプターパターン
`agent/source/interfaces/`で抽象化レイヤーを提供し、外部サービスの差し替えを容易に。

#### 4. 非同期処理
FastAPIの非同期機能を活用し、Google Drive同期やLLM API呼び出しをブロッキングせずに実行。

---

## 🚀 主要機能の技術的詳細

### 1. Google Drive連携

#### OAuth 2.0認証フロー
```python
# 1. ユーザーがGoogleログインボタンをクリック
# 2. Google認証画面へリダイレクト
# 3. 認証成功後、コールバックURLへトークンを受け取り
# 4. トークンを使用してGoogle Drive APIにアクセス
```

#### 自動ファイル同期
- フォルダ構造認識（`datasets/`, `paper/`, `poster/`）
- ファイルハッシュによる重複排除
- メタデータの自動保存（Google Drive URL含む）

#### 実装の工夫
- **リトライ機構**: API制限に対する指数バックオフ
- **バッチ処理**: 大量ファイルの効率的な処理
- **差分同期**: 変更されたファイルのみを更新

### 2. ベクトル検索（RAG）

#### セマンティック検索の仕組み

```
┌──────────────────┐
│  ユーザークエリ   │ "機械学習のデータセット"
└────────┬─────────┘
         │
         ▼
┌────────────────────────┐
│ Embedding Model        │ sentence-transformers/all-MiniLM-L6-v2
│ (384次元ベクトル化)     │
└────────┬───────────────┘
         │
         ▼
┌────────────────────────┐
│ ChromaDB              │
│ コサイン類似度計算     │
└────────┬───────────────┘
         │
         ▼
┌────────────────────────┐
│ 関連文書Top-K取得      │ 類似度スコア付き
└────────────────────────┘
```

#### ハイブリッド検索
ベクトル検索が利用不可の場合、TF-IDFによるキーワード検索にフォールバック。

### 3. AI研究相談（RAG + LLM）

#### RAGパイプライン

```python
def research_consultation(query: str) -> str:
    # 1. ベクトル検索で関連文書を取得
    relevant_docs = vector_search(query, top_k=5)

    # 2. コンテキストを構築
    context = build_context(relevant_docs)

    # 3. LLMにプロンプトを送信
    prompt = f"""
    あなたは研究アドバイザーです。
    以下の研究データを参照して質問に答えてください。

    【研究データ】
    {context}

    【質問】
    {query}
    """

    # 4. OpenRouter API経由でLLM呼び出し
    response = openrouter_client.chat(prompt)

    return response
```

#### スマート関連性フィルタリング
- **キーワード抽出**: クエリから重要キーワードを抽出
- **ストップワード除去**: 一般的すぎる単語を除外
- **スコアリング**: 関連性スコアに基づいて推薦精度を向上
- **閾値フィルタリング**: スコア5以上のアイテムのみ表示

### 4. マルチLLMプロバイダ対応

#### OpenRouter API統合
単一のAPIで複数のLLMモデルを利用可能：
- Claude 3.5 Sonnet
- GPT-4
- Gemini 2.0 Flash

#### モデル自動同期
24時間ごとにOpenRouterのモデル一覧を自動取得し、データベースに保存。

---

## ⚡ クイックスタート

### 1. 依存関係のインストール

```bash
# uvを使用（推奨）
uv sync --dev
```

### 2. 環境変数の設定

```bash
# .envファイルを作成
cp .env.example .env

# 必須項目を編集
vim .env
```

必要な環境変数：
```env
# OpenRouter API（必須）
OPENROUTER_API_KEY=your_api_key_here
OPENROUTER_MODEL=openrouter/anthropic/claude-3.5-sonnet

# Google OAuth（オプション）
GOOGLE_OAUTH_CLIENT_ID=your_client_id
GOOGLE_OAUTH_CLIENT_SECRET=your_client_secret

# ベクトル検索（オプション、推奨）
ENABLE_VECTOR_SEARCH=true
```

### 3. Webアプリケーション起動

```bash
# メインアプリケーション起動
uvicorn app.main:app --reload

# ブラウザでアクセス
# http://localhost:8000
```

### 4. Google Drive連携（オプション）

1. [Google Cloud Console](https://console.cloud.google.com/)でOAuth 2.0クライアントIDを作成
2. リダイレクトURIに `http://localhost:8000/api/auth/google/callback` を追加
3. `.env`にクライアントIDとシークレットを設定
4. WebUIから「Googleでログイン」をクリック

### 5. ベクトルインデックス作成

```bash
# 全ドキュメントのベクトルインデックスを作成
curl -X POST http://localhost:8000/api/vector/index
```

---

## 🔧 開発環境

### APIサーバー起動

```bash
# 開発用APIサーバー（認証なし）
uv run python services/api/paas_api.py

# 本番用APIサーバー（認証あり）
uv run python services/api/paas_api_with_auth.py
```

### テスト実行

```bash
# 全テスト実行
uv run pytest agent/tests/ -v

# カバレッジ付き
uv run pytest agent/tests/ --cov=agent/source --cov-report=html
```

### コード品質チェック

```bash
# リンター
uv run ruff check agent/

# フォーマット
uv run ruff format agent/

# 型チェック
uv run mypy agent/
```

---

## 📊 データベース構造

### 主要テーブル

#### datasets（データセット）
```sql
CREATE TABLE datasets (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    file_count INTEGER DEFAULT 0,
    total_size INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    summary TEXT,
    drive_folder_id TEXT,
    drive_url TEXT
);
```

#### papers（論文）
```sql
CREATE TABLE papers (
    id INTEGER PRIMARY KEY,
    file_path TEXT UNIQUE NOT NULL,
    file_name TEXT NOT NULL,
    file_size INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    indexed_at TIMESTAMP,
    title TEXT,
    authors TEXT,
    abstract TEXT,
    keywords TEXT,
    content_hash TEXT,
    drive_file_id TEXT,
    drive_url TEXT
);
```

#### dataset_files（データセット内ファイル）
```sql
CREATE TABLE dataset_files (
    id INTEGER PRIMARY KEY,
    dataset_id INTEGER NOT NULL,
    file_path TEXT UNIQUE NOT NULL,
    file_name TEXT NOT NULL,
    file_type TEXT,
    file_size INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    indexed_at TIMESTAMP,
    content_hash TEXT,
    schema_info TEXT,
    summary TEXT,
    drive_file_id TEXT,
    drive_url TEXT,
    FOREIGN KEY (dataset_id) REFERENCES datasets(id)
);
```

#### openrouter_models（LLMモデル情報）
```sql
CREATE TABLE openrouter_models (
    id INTEGER PRIMARY KEY,
    model_id TEXT UNIQUE NOT NULL,
    model_name TEXT NOT NULL,
    description TEXT,
    context_length INTEGER,
    pricing_prompt REAL,
    pricing_completion REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    top_provider TEXT,
    architecture TEXT,
    modality TEXT,
    visible BOOLEAN DEFAULT 1
);
```

---

## 🌐 API エンドポイント

### Web UI API

#### Google Drive同期
- `POST /api/sync/google-drive` - Google Drive同期開始
- `GET /api/google-drive/status` - 同期状態確認
- `GET /api/drive/folders` - フォルダ一覧取得

#### 検索・相談
- `POST /api/search` - 研究データ検索（ハイブリッド）
- `POST /api/consultation` - AI研究相談（RAG対応）
- `POST /api/vector/search` - セマンティック検索

#### データベース情報
- `GET /api/database/summary` - データベース詳細要約
- `GET /api/datasets/{dataset_id}` - データセット詳細取得
- `GET /api/datasets/{dataset_id}/files` - ファイル一覧

#### OpenRouterモデル管理
- `GET /api/models` - モデル一覧取得
- `POST /api/models/sync` - モデル一覧手動同期

### PaaS API

開発用（認証なし）と本番用（認証あり）の2つのAPIサーバーを提供：

- `GET /health` - ヘルスチェック
- `POST /documents/ingest` - 文書取り込み
- `GET /documents/search` - 文書検索
- `GET /documents/{category}/{document_id}` - 文書詳細取得
- `GET /statistics` - システム統計情報

---

## 🎓 技術的な実装ポイント

### 1. 循環インポート回避
Analyzerは遅延インポートすることで、IndexerとAnalyzerの循環依存を回避。

```python
# agent/source/indexer/new_indexer.py
def analyze_if_needed(self, category: str):
    # 遅延インポートで循環参照を回避
    from agent.source.analyzer.new_analyzer import NewFileAnalyzer
    analyzer = NewFileAnalyzer()
    analyzer.analyze_unanalyzed_files(category)
```

### 2. リポジトリパターン
データアクセスロジックをリポジトリクラスに集約し、ビジネスロジックから分離。

```python
# agent/source/database/new_repository.py
class PaperRepository:
    def find_all(self) -> List[Paper]:
        pass

    def find_by_id(self, paper_id: int) -> Optional[Paper]:
        pass

    def save(self, paper: Paper) -> Paper:
        pass
```

### 3. FastAPIバックグラウンドタスク
長時間処理をバックグラウンドで実行し、UIのレスポンスを保つ。

```python
from fastapi import BackgroundTasks

@app.post("/api/sync/google-drive")
async def sync_google_drive(background_tasks: BackgroundTasks):
    background_tasks.add_task(execute_sync)
    return {"status": "started"}
```

### 4. OpenRouterモデル自動同期
アプリケーション起動時にバックグラウンドタスクとして24時間ごとに実行。

```python
@app.on_event("startup")
async def startup_event():
    background_tasks.add_task(sync_openrouter_models_periodically)
```

---

## 📚 設定オプション

### 基本設定
- `DATABASE_PATH`: SQLiteデータベースパス（開発環境）
- `DATABASE_URL`: PostgreSQL接続URL（本番環境）
- `DATA_DIR_PATH`: ローカルデータディレクトリ

### LLM API設定
- `OPENROUTER_API_KEY`: OpenRouter APIキー（必須）
- `OPENROUTER_MODEL`: 使用するモデル（デフォルト: `openrouter/anthropic/claude-3.5-sonnet`）
- `GEMINI_API_KEY`: Google Gemini APIキー（レガシー）

### ベクトル検索設定
- `ENABLE_VECTOR_SEARCH`: ベクトル検索有効化（`true`/`false`）
- `VECTOR_DB_PROVIDER`: プロバイダー（`chroma`）
- `VECTOR_EMBEDDING_MODEL`: 埋め込みモデル（`sentence-transformers/all-MiniLM-L6-v2`）

### Google Drive連携設定
- `GOOGLE_DRIVE_CREDENTIALS_PATH`: 認証情報ファイルパス
- `GOOGLE_DRIVE_FOLDER_IDS`: 同期対象フォルダID（JSON配列）
- `GOOGLE_DRIVE_MAX_FILE_SIZE_MB`: 最大ファイルサイズ（デフォルト: `100`MB）

### 認証設定
- `AUTH_ENABLED`: 認証機能有効化（`true`/`false`）
- `GOOGLE_OAUTH_CLIENT_ID`: OAuth 2.0クライアントID
- `GOOGLE_OAUTH_CLIENT_SECRET`: OAuth 2.0クライアントシークレット
- `ALLOWED_DOMAINS`: 許可ドメイン（カンマ区切り）

詳細な設定オプションは[CLAUDE.md](CLAUDE.md)を参照してください。

---

## 🤝 貢献

プルリクエストやイシューの報告を歓迎します。

## 📄 ライセンス

研究・教育目的での利用を前提としています。

---

<div align="center">
  <strong>AIとクラウドで、研究データ管理を次のレベルへ</strong>
</div>
