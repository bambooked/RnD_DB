# 研究データ管理システム - R&D DB

Google Drive連携 & スマート推薦搭載 AI研究相談システム

## 概要

Google Drive連携とAI（Google Gemini + セマンティック検索）を活用した研究相談機能を備えた、完全なWebベースの研究データ管理システムです。研究者が論文、ポスター、データセットを効率的に管理し、**最新のベクトル検索技術とスマート関連性フィルタリング**でリアルタイムにAI相談を受けられます。関連性の高いアイテムのみを推薦し、Google Driveへの直接リンクでワンクリックアクセスを実現します。

## 主要機能

### 🌐 **Webアプリケーション**
- **FastAPI**ベースの高性能WebAPI
- **レスポンシブWebUI**: TailwindCSSを使用したモダンなインターフェース
- **OAuth 2.0認証**: Googleアカウントでのシームレスなログイン
- **リアルタイム同期**: Google Driveとの自動同期機能
- **バックグラウンド処理**: 非同期でのファイル処理

### ☁️ **Google Drive連携（Web OAuth）**
- **簡単ログイン**: Googleアカウントでワンクリックログイン
- **フォルダ選択**: Web UI上でGoogle Driveフォルダを選択
- **自動ファイル同期**: 選択したフォルダから自動インポート
- **セキュアな認証**: OAuth 2.0による安全な認証フロー
- **フォルダ構造対応**: datasets/paper/posterフォルダの自動識別
- **直接リンク**: 論文・ポスター・データセットへのGoogle Drive URLを自動保存
- **ワンクリックアクセス**: UI上の「開く」ボタンでGoogle Driveへ直接ジャンプ

### 🤖 **AI研究相談（RAG + LLM）**
- **セマンティック検索RAG**: ChromaDB + sentence-transformers による意味理解
- **ハイブリッド検索**: ベクトル検索とTF-IDFの組み合わせ
- **完全LLM駆動**: Google Gemini APIによる動的な研究アドバイス
- **コンテキスト検索**: 既存データベースを参照した的確な助言
- **研究計画支援**: プロジェクト計画から実行まで包括的サポート
- **関連文書提示**: 質問に関連する論文・データセットを自動抽出
- **スマート関連性フィルタリング**: 関連性スコアに基づく精度の高い推薦
- **Google Driveリンク**: 各アイテムへの直接アクセス可能

### 🔍 **高度な検索機能（ベクトル検索対応）**
- **セマンティック検索**: 意味ベースの高精度検索
- **統合検索**: 論文、ポスター、データセットを横断検索
- **埋め込みモデル**: sentence-transformers/all-MiniLM-L6-v2
- **フォールバック**: ベクトル検索が利用不可時はTF-IDFで対応
- **リアルタイム結果**: 即座に検索結果を表示

### 📊 **データ管理**
- **自動メタデータ抽出**: ファイルから自動的に情報を抽出
- **統計ダッシュボード**: 登録データの統計情報をリアルタイム表示
- **重複防止**: UNIQUE制約による重複登録防止

## 技術スタック

### バックエンド
- **Python 3.11+**: プログラミング言語
- **FastAPI**: 高性能WebAPIフレームワーク
- **uvicorn**: ASGI サーバー
- **uv**: パッケージ管理・環境管理ツール
- **SQLite**: 開発環境データベース
- **PostgreSQL**: 本番環境データベース（実装済み、設定で有効化）
- **Google APIs**: Drive API, Gemini API
- **ChromaDB**: ベクトルデータベース（ローカル開発）
- **Pinecone**: ベクトルデータベース（オプション、クラウド運用）
- **sentence-transformers**: 埋め込みモデル（all-MiniLM-L6-v2）
- **scikit-learn**: 機械学習・検索機能（TF-IDF）

### フロントエンド
- **HTML5/CSS3/JavaScript**: モダンWeb技術
- **TailwindCSS**: ユーティリティファーストCSSフレームワーク
- **Font Awesome**: アイコンライブラリ
- **Chart.js**: データ可視化
- **Jinja2**: テンプレートエンジン

### インフラ・統合
- **Google Drive API**: クラウドストレージ連携
- **OAuth 2.0**: セキュアな認証（Web認証フロー）
- **JWT**: セッション管理・トークン認証
- **PyTorch**: 機械学習バックエンド（MPS/CUDA対応）
- **Docker**: コンテナ化（未実装）
- **Render.com**: PaaSデプロイ先（未実装）

### 開発ツール
- **pytest**: テストフレームワーク
- **pytest-asyncio**: 非同期テスト
- **pytest-cov**: テストカバレッジ
- **ruff**: リンター・フォーマッター
- **mypy**: 型チェック

## クイックスタート

### 1. 依存関係のインストール

```bash
# uvを使用（推奨）
uv sync --dev

# または pip
pip install chromadb sentence-transformers fastapi uvicorn python-dotenv google-api-python-client google-auth-oauthlib scikit-learn pypdf2
```

### 2. 環境設定

```bash
# 環境変数ファイルを編集
vim .env

# 必須項目
GEMINI_API_KEY=your_gemini_api_key
ENABLE_VECTOR_SEARCH=true  # ベクトル検索を有効化

# Google OAuth設定（Web OAuth用）
OAUTH_CLIENT_ID=your_oauth_client_id
OAUTH_CLIENT_SECRET=your_oauth_client_secret
OAUTH_REDIRECT_URI=http://localhost:8000/api/auth/google/callback
```

### 3. Google OAuth設定（Web認証）

1. [Google Cloud Console](https://console.cloud.google.com/)でプロジェクト作成
2. **OAuth 2.0 クライアント ID**を作成（Webアプリケーション）
3. 承認済みのリダイレクトURIに`http://localhost:8000/api/auth/google/callback`を追加
4. クライアントIDとシークレットを`.env`に設定
5. Drive APIを有効化

### 4. Webアプリ起動

```bash
# メインWebアプリケーション起動
uvicorn web_app:app --reload

# または uvコマンド経由
uv run uvicorn web_app:app --host 0.0.0.0 --port 8000 --reload
```

### 5. アクセス & 初期設定

1. ブラウザで http://localhost:8000 にアクセス
2. **「同期」ボタン** → **「Googleでログイン」**をクリック
3. Googleアカウントでログイン
4. Google Driveフォルダを選択
5. **「同期開始」**でデータをインポート

### 6. ベクトルインデックス作成

```bash
# 全ドキュメントのベクトルインデックスを作成
curl -X POST http://localhost:8000/api/vector/index

# または、Web UIから初回同期時に自動作成
```

## API エンドポイント

### Web アプリケーション (web_app.py)

#### システム状態
- `GET /api/status` - システム状態確認
- `GET /api/vector/status` - ベクトル検索状態確認
- `GET /api/database/summary` - データベース詳細要約

#### Google OAuth認証
- `GET /api/auth/google/login` - Google認証開始
- `GET /api/auth/google/callback` - OAuth コールバック
- `GET /api/auth/google/status` - 認証状態確認
- `GET /api/google-drive/status` - Google Drive状態確認

#### データ同期
- `POST /api/sync/google-drive` - Google Drive同期実行
- `GET /api/drive/folders` - Driveフォルダ一覧取得

#### ベクトル検索（新機能）
- `POST /api/vector/index` - 全ドキュメントのインデックス作成
- `POST /api/vector/search` - セマンティック検索実行

#### 検索・相談
- `POST /api/search` - 研究データ検索（ハイブリッド）
- `POST /api/consultation` - AI研究相談（RAG対応）

### PaaS API (services/api/)

開発用と本番用の2つのAPIサーバーを提供:

#### 開発用API (paas_api.py) - 認証なし
```bash
# 起動
uv run python services/api/paas_api.py
```

- `GET /health` - ヘルスチェック
- `POST /api/search` - 文書検索
- `POST /api/analyze` - ファイル解析
- `GET /api/stats` - 統計情報取得
- `POST /api/index/update` - インデックス更新

#### 本番用API (paas_api_with_auth.py) - 認証あり
```bash
# 起動（環境変数で認証設定が必要）
uv run python services/api/paas_api_with_auth.py
```

上記に加えて認証機能が有効化されます。

## 使用例

### スマート推薦の仕組み

質問に対して関連性の高いアイテムのみを推薦します：

```javascript
// ユーザーの質問: "LLMのバイアスに関する研究を教えて"

// システムの動作:
// 1. キーワード抽出: ["llm", "バイアス"]
// 2. stopwords除外: ["研究", "教えて"] → 除外
// 3. スコアリング:
//    - jbbq: "LLM" + "バイアス" 一致 → スコア6 → ✅ 表示
//    - esg: キーワード不一致 → スコア0 → ❌ 非表示
//    - tv_efect: 一般的単語のみ一致 → スコア3 → ❌ 非表示

// 結果: 関連性の高いjbbqデータセットのみを表示
```

### Google Drive直接アクセス

各アイテムに「開く」ボタンが表示され、Google Driveへワンクリックでアクセスできます：

```html
<!-- UI表示例 -->
<div class="research-item">
  <h3>JBBQ (Japanese Bias Benchmark for QA)</h3>
  <p>日本語LLMのバイアス（偏見）検証用データセット</p>
  <button onclick="window.open('https://drive.google.com/...')">
    <i class="fas fa-external-link-alt"></i> 開く
  </button>
</div>
```

## 機能詳細

### ベクトル検索（セマンティック検索）
```bash
# インデックス作成
curl -X POST http://localhost:8000/api/vector/index

# セマンティック検索
curl -X POST http://localhost:8000/api/vector/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "machine learning datasets",
    "limit": 5,
    "threshold": 0.3
  }'

# レスポンス例
{
  "success": true,
  "query": "machine learning datasets",
  "results": [
    {
      "id": "paper_1",
      "similarity": 0.856,
      "type": "paper",
      "title": "Deep Learning for Image Classification",
      "metadata": {...}
    }
  ],
  "count": 5
}
```

### AI研究相談（RAG対応）
```javascript
// 相談リクエスト例（自動的にベクトル検索を使用）
{
  "query": "機械学習を使ったデータ分析について相談したい",
  "consultation_type": "database"  // "general", "database", "planning"
}

// システムは自動的に：
// 1. ベクトル検索で関連文書を取得
// 2. 関連文書をコンテキストとしてLLMに渡す
// 3. 的確なアドバイスを生成
```

### ハイブリッド検索
```javascript
// 統合検索（ベクトル優先、フォールバックでTF-IDF）
{
  "query": "深層学習",
  "search_type": "papers"  // "all", "papers", "posters", "datasets"
}
```

## プロジェクト構造

```
RnD_DB/
├── web_app.py                      # メインWebアプリケーション（エントリーポイント）
├── templates/
│   ├── base.html                  # 全ページ共通レイアウト
│   ├── dashboard.html             # ダッシュボード
│   ├── chat.html                  # AI研究相談チャット
│   ├── search.html                # 研究データ検索
│   ├── drive_sync.html            # Google Drive同期
│   └── settings.html              # 設定ダッシュボード
├── static/                        # 静的ファイル（CSS/JS/画像）
├── services/                      # API・サービス層
│   ├── api/                       # HTTP APIエンドポイント
│   │   ├── paas_api.py           # 開発用APIサーバー（認証なし）
│   │   └── paas_api_with_auth.py # 本番用APIサーバー（認証あり）
│   ├── rag_interface.py          # RAG統合インターフェース
│   └── enhanced_rag_interface.py # 拡張RAGインターフェース
├── agent/                         # コアアプリケーション
│   ├── source/                   # 核心モジュール
│   │   ├── ui/                   # UIコントローラー
│   │   │   └── interface.py      # UserInterface（メインコントローラー）
│   │   ├── indexer/              # インデクサー
│   │   │   ├── new_indexer.py    # 新ファイルインデクサー
│   │   │   └── scanner.py        # ファイルスキャナー
│   │   ├── analyzer/             # アナライザー
│   │   │   ├── new_analyzer.py   # 新アナライザー（Gemini API）
│   │   │   └── gemini_client.py  # Gemini APIクライアント
│   │   ├── database/             # データベース関連
│   │   │   ├── connection.py     # DB接続管理
│   │   │   ├── new_models.py     # データモデル
│   │   │   └── new_repository.py # リポジトリパターン
│   │   ├── integrations/         # クラウド連携機能
│   │   │   ├── google_drive.py   # Google Drive連携
│   │   │   └── looker_export.py  # データエクスポート
│   │   ├── advisor/              # AI相談機能
│   │   │   └── enhanced_research_advisor.py  # RAG + 関連性フィルタリング
│   │   └── interfaces/           # 並行開発用抽象化レイヤー
│   │       ├── data_models.py    # 共通データ型定義
│   │       ├── input_ports.py    # データ入力インターフェース
│   │       ├── search_ports.py   # 検索機能インターフェース
│   │       ├── auth_ports.py     # 認証・認可インターフェース
│   │       ├── service_ports.py  # サービス統合インターフェース
│   │       ├── config_ports.py   # 設定管理インターフェース
│   │       ├── vector_search_impl.py  # ChromaDBベクトル検索実装
│   │       ├── vector_indexer.py      # ベクトルインデックス管理
│   │       ├── vector_service.py      # ベクトル検索統合サービス
│   │       └── google_drive_impl.py   # Google Drive入力ポート実装
│   ├── tests/                    # エージェント関連テスト
│   └── database/
│       └── research_data.db      # SQLiteデータベース
├── tools/                        # 実行可能ツール・設定
│   ├── config.py                 # 設定ファイル
│   └── agent/                    # エージェント関連ツール
├── tests/                        # 統合テスト
│   └── integration/              # 統合テストスイート
│       └── test_paas_integration.py
├── data/                         # 研究データ
│   ├── datasets/                 # データセット（CSV/JSON/JSONL）
│   ├── paper/                    # 論文PDF
│   └── poster/                   # ポスターPDF
├── chroma_db/                    # ベクトルDB永続化ディレクトリ
├── credentials/                  # 認証情報（.gitignore）
│   ├── google_drive_credentials.json  # OAuth Client ID
│   ├── google_oauth_token.json        # 保存されたトークン
│   └── client_secret.json             # OAuth設定
├── scripts/                      # テスト・デバッグスクリプト
│   ├── check_response.py         # API応答テスト
│   ├── test_sync.py              # Drive同期テスト
│   └── migrate_add_drive_urls.py # マイグレーションスクリプト
├── docs/                         # ドキュメント
├── .env                          # 環境設定（開発環境）
├── .env.production               # 環境設定（本番環境）
├── pyproject.toml                # プロジェクト設定（uv）
├── CLAUDE.md                     # Claude Code用プロジェクト指針
└── README.md                     # このファイル
```

## 設定オプション

### 開発環境設定（.env）

#### 基本設定
- `GEMINI_API_KEY`: Google Gemini APIキー（必須）
- `GEMINI_MODEL`: 使用するモデル（デフォルト: `gemini-2.0-flash-exp`）
- `DATABASE_PATH`: SQLiteデータベースパス
- `DATA_DIR_PATH`: ローカルデータディレクトリ

#### ベクトル検索設定
- `VECTOR_SEARCH_ENABLED`: ベクトル検索有効化（`false`/`true`）
- `VECTOR_DB_PROVIDER`: プロバイダー（`chroma`）
- `VECTOR_COLLECTION_NAME`: コレクション名（`research_documents`）
- `ENABLE_VECTOR_SEARCH`: ベクトル検索有効化（`true`推奨）
- `VECTOR_SEARCH_PROVIDER`: プロバイダー（`chroma`）
- `VECTOR_EMBEDDING_MODEL`: 埋め込みモデル（`sentence-transformers/all-MiniLM-L6-v2`）
- `VECTOR_DIMENSION`: ベクトル次元（`384`）

#### PaaS API設定
- `API_HOST`: APIホスト（デフォルト: `0.0.0.0`）
- `API_PORT`: APIポート（デフォルト: `8000`）

#### PaaS統合機能設定
- `PAAS_ENABLE_GOOGLE_DRIVE`: Google Drive連携有効化（`false`/`true`）
- `PAAS_ENABLE_VECTOR_SEARCH`: ベクトル検索有効化（`false`/`true`）
- `PAAS_ENABLE_AUTHENTICATION`: 認証機能有効化（`false`/`true`）

#### Google Drive連携設定
- `GOOGLE_DRIVE_CREDENTIALS_PATH`: 認証情報ファイルパス
- `GOOGLE_DRIVE_MAX_FILE_SIZE_MB`: 最大ファイルサイズ（デフォルト: `100`MB）
- `GOOGLE_DRIVE_SYNC_INTERVAL`: 同期間隔（デフォルト: `60`秒）

#### Google OAuth設定
- `OAUTH_CLIENT_ID`: OAuth 2.0 クライアントID
- `OAUTH_CLIENT_SECRET`: OAuth 2.0 クライアントシークレット
- `OAUTH_REDIRECT_URI`: リダイレクトURI（`http://localhost:8000/api/auth/google/callback`）

#### 認証設定（開発環境）
- `AUTH_ENABLED`: 認証有効化（`false`）
- `JWT_SECRET_KEY`: JWT秘密鍵（開発用）
- `ALLOWED_DOMAINS`: 許可ドメイン（カンマ区切り）

#### パフォーマンス設定
- `CHAT_HISTORY_LIMIT`: チャット履歴保持数
- `MAX_RESPONSE_LENGTH`: AI応答最大長
- `SIMILARITY_THRESHOLD`: 検索類似度閾値（ベクトル検索: 0.3-0.5推奨）

### 本番環境設定（.env.production）

#### データベース設定
- `DATABASE_URL`: PostgreSQL接続URL（`postgresql://user:pass@host/db`）
- `DATABASE_POOL_SIZE`: 接続プールサイズ（デフォルト: `10`）

#### ベクトル検索設定
- `ENABLE_VECTOR_SEARCH`: `true` でベクトル検索を有効化
- `VECTOR_SEARCH_PROVIDER`: `chroma`（ローカル、デフォルト）または `pinecone`
- `VECTOR_SEARCH_API_KEY`: プロバイダに応じたAPIキー（Pinecone利用時は必須）
- `VECTOR_EMBEDDING_MODEL`: SentenceTransformersのモデル名（例: `sentence-transformers/all-MiniLM-L6-v2`）

#### 認証設定（Google OAuth2）
- `GOOGLE_CLIENT_ID`: Google OAuth2 クライアントID
- `GOOGLE_CLIENT_SECRET`: Google OAuth2 クライアントシークレット
- `JWT_SECRET_KEY`: JWT秘密鍵（32文字以上推奨）

#### セキュリティ設定
- `ALLOWED_ORIGINS`: CORS許可オリジン（JSON配列）
- `RATE_LIMIT_ENABLED`: レート制限有効化（`true`推奨）

### 関連性フィルタリング設定
- **データセット推薦閾値**: スコア5以上（重要キーワード2つ以上一致 or データセット名一致）
- **stopwords**: 一般的すぎる単語を除外（「研究」「分析」「データ」など）
- **推薦精度**: 関連性の高いアイテムのみを表示

## 開発コマンド

### 基本開発
```bash
# 環境セットアップ
uv sync --dev

# Webアプリケーション起動（メインエントリーポイント）
uvicorn web_app:app --reload

# PaaS APIサーバー起動（開発用）
uv run python services/api/paas_api.py

# PaaS APIサーバー起動（本番用・認証あり）
uv run python services/api/paas_api_with_auth.py
```

### テスト実行
```bash
# 全テスト実行
uv run pytest agent/tests/ -v

# カバレッジ付きテスト
uv run pytest agent/tests/ --cov=agent/source --cov-report=html

# 非同期テスト
uv run pytest agent/tests/ --asyncio-mode=auto

# 単一テスト実行
uv run pytest agent/tests/test_indexer.py::test_scan_files -v
```

### コード品質チェック
```bash
# リンターチェック
uv run ruff check agent/

# フォーマット
uv run ruff format agent/

# 型チェック
uv run mypy agent/
```

### データ操作
```bash
# インデックス更新（全ファイル再スキャン）
uv run python -c "from agent.source.ui.interface import UserInterface; ui = UserInterface(); ui.update_index()"

# 解析状況確認
uv run python -c "from agent.source.ui.interface import UserInterface; ui = UserInterface(); summary = ui.analyzer.get_analysis_summary(); print(summary)"

# 特定カテゴリー未解析ファイル解析
uv run python -c "from agent.source.analyzer.new_analyzer import NewFileAnalyzer; analyzer = NewFileAnalyzer(); analyzer.analyze_unanalyzed_files('dataset')"

# PaaS統合テスト
uv run python tests/integration/test_paas_integration.py
```

### デプロイメント（未実装）
```bash
# ローカル開発環境（Docker）- 未実装
# docker-compose up -d
# docker-compose logs -f

# 本番デプロイ（Render.com）- 未実装
# ./scripts/deploy.sh -e production

# データベース移行（SQLite → PostgreSQL）- 未実装
# python migration/sqlite_to_postgresql.py --postgresql-url=$DATABASE_URL
```

## アーキテクチャ設計

### モジュール依存関係
```
External Systems
  └─> web_app.py (Main Web Application with Google Drive)
       ├─> services/api/paas_api_with_auth.py (Production API with Auth)
       │    └─> services/api/paas_api.py (FastAPI HTTP API)
       │         └─> services/rag_interface.py (RAG Abstraction Layer)
       └─> agent/source/ui/interface.py (UserInterface)
            ├─> indexer/new_indexer.py (NewFileIndexer)
            │    ├─> scanner.py (FileScanner)
            │    └─> analyzer/new_analyzer.py (遅延ロード)
            ├─> analyzer/new_analyzer.py (NewFileAnalyzer)
            │    ├─> gemini_client.py (GeminiClient)
            │    └─> database/new_repository.py
            ├─> database/new_repository.py
            │    ├─> DatasetRepository
            │    ├─> PaperRepository
            │    └─> PosterRepository
            └─> integrations/google_drive.py (Google Drive連携)
```

### 重要な設計決定
1. **循環インポート回避**: AnalyzerはIndexer内で遅延インポート
2. **カテゴリー別処理**: データセット、論文、ポスターで異なるテーブル・処理
3. **自動解析**: `auto_analyze=True`でファイル登録時に自動Gemini API解析
4. **データセット単位管理**: ディレクトリをデータセットとして扱う
5. **PaaS統合**: HTTP API経由で外部システムから利用可能
6. **本番環境**: PostgreSQL、クラウド向けベクトルDB（Pinecone等）、認証機能有効化
7. **Google Drive連携**: サービスアカウント認証による自動同期
8. **ベクトル検索**: ChromaDB（開発）/Pinecone（本番想定）によるセマンティック検索

### データベース構造（新設計）

#### カテゴリー別テーブル
- **datasets**: データセット情報
  - `id`, `name`, `summary`, `file_count`, `total_size`, `created_at`
- **papers**: 論文
  - `id`, `title`, `authors`, `abstract`, `keywords`, `file_path`, `created_at`
- **posters**: ポスター
  - `id`, `title`, `authors`, `abstract`, `keywords`, `file_path`, `created_at`
- **dataset_files**: データセット内ファイル
  - `id`, `dataset_id` (外部キー), `file_path`, `file_size`, `created_at`

#### 本番環境追加テーブル（実装済み、設定で有効化）
- **users**: ユーザー情報（Google OAuth2）
- **user_sessions**: セッション管理
- **vector_metadata**: ベクトル検索メタデータ
- **audit_log**: 監査ログ
- **system_events**: システムイベント

### 並行開発用インターフェース（agent/source/interfaces/）

Claude Code並行開発用の抽象化レイヤーを提供:

- **data_models.py**: 共通データ型定義
- **input_ports.py**: データ入力インターフェース（Google Drive, Upload）
- **search_ports.py**: 検索機能インターフェース（Vector, Semantic, Hybrid）
- **auth_ports.py**: 認証・認可インターフェース（OAuth2, RBAC）
- **service_ports.py**: サービス統合インターフェース（Orchestration）
- **config_ports.py**: 設定管理インターフェース（Environment, Features）
- **vector_search_impl.py**: ChromaDBベクトル検索実装
- **google_drive_impl.py**: Google Drive入力ポート実装

#### 実装原則
1. **非破壊的拡張**: 既存システムは絶対に変更しない
2. **完全独立性**: 各ポートは他に依存しない設計
3. **フォールバック必須**: 新機能失敗時は既存システムで継続
4. **設定制御**: 全新機能は設定でON/OFF可能

## トラブルシューティング

### ベクトル検索が動作しない
1. `ENABLE_VECTOR_SEARCH=true`が設定されているか確認
2. ChromaDBとsentence-transformersがインストールされているか確認
   ```bash
   uv add chromadb sentence-transformers
   ```
3. インデックスが作成されているか確認
   ```bash
   curl -X POST http://localhost:8000/api/vector/index
   ```
4. ログを確認（`tail -f /tmp/rndd_server.log`）

### Google OAuth認証エラー
1. OAuth Client IDとSecretが正しいか確認
2. リダイレクトURIがGoogle Cloud Consoleで設定されているか確認
3. Drive APIが有効化されているか確認
4. ブラウザのCookieをクリア

### AI相談が動作しない
1. Gemini APIキーの確認
2. ネットワーク接続の確認
3. リクエスト制限の確認
4. ベクトル検索が有効かどうか確認（有効な場合、より精度の高い検索結果）

### 検索結果が出ない
1. データベース内容の確認（`GET /api/status`）
2. ベクトルインデックスが作成されているか確認
3. 閾値（threshold）を下げてテスト（0.3推奨）
4. フォールバックTF-IDF検索が動作しているか確認

### 関連性の低いアイテムが表示される / 関連性の高いアイテムが表示されない
1. **データセットのdescriptionを確認**:
   - 重要なキーワードがdescriptionに含まれているか確認
   - 例: JBBQなら「LLM」「バイアス」「bias」などを含める
   ```sql
   UPDATE datasets SET description = 'JBBQ (Japanese Bias Benchmark for QA) は日本語LLMのバイアス検証用データセット' WHERE name = 'jbbq';
   ```

2. **stopwordsの確認**:
   - `agent/source/advisor/enhanced_research_advisor.py` の stopwords を確認
   - 一般的すぎる単語が除外されているか確認

3. **関連性スコアの調整**:
   - 現在の閾値: データセット = 5, 論文/ポスター = ベクトル類似度ベース
   - `enhanced_research_advisor.py:512` で閾値変更可能

## データディレクトリ構造

プロジェクトでは以下のデータディレクトリ構造を使用します:

```
data/
├── datasets/        # データセット（CSV/JSON/JSONL）
│   ├── cm-effect/   # CMエフェクトデータ
│   ├── data-analysis/ # データ分析JSONファイル
│   ├── dataset/     # サンプルデータセット
│   ├── esg/         # 企業サステナビリティデータ（19ファイル、247MB）
│   ├── greendata/   # 環境排出量データ（2ファイル、1.6MB）
│   ├── jbbq/        # 日本語LLMバイアス研究（5ファイル、44MB）
│   ├── tv-rating/   # TV視聴率データ
│   └── tv_efect/    # TV効果データ（2ファイル、0.2MB）
├── paper/           # 論文PDF
└── poster/          # ポスターPDF
```

各データセットはディレクトリ単位で管理され、データベースに登録されます。

## 重要な注意事項

1. **新データベース構造の使用**: 旧`files`テーブルは使用せず、カテゴリー別テーブルを使用
2. **自動解析の実行**: `auto_analyze=True`でファイル登録時に自動的にGemini API解析が実行される
3. **データセット要約形式**: 必ず「このデータセットは～」で開始する形式
4. **agent/main.py は存在しない**: メインエントリーポイントは`web_app.py`
5. **テスト更新が必要**: 一部テストが旧データベース構造を対象としているため要更新
6. **環境変数の確認**: 開発環境と本番環境で異なる設定ファイル（.env, .env.production）を使用

## ライセンス

研究・教育目的での利用を前提としています。

## 貢献

プルリクエストやイシューの報告を歓迎します。

## 実装状況

### ✅ 完全実装済み機能

#### コア機能
- **ファイルインデクサー**: カテゴリー別ファイルスキャン・登録
- **Gemini API解析**: 論文・ポスター・データセットの自動メタデータ抽出
- **新データベース構造**: カテゴリー別テーブル設計（datasets, papers, posters, dataset_files）
- **自動解析**: ファイル登録時の自動AI解析

#### Web アプリケーション
- **FastAPI Webアプリ**: メインエントリーポイント（web_app.py）
- **Google Drive連携**: OAuth 2.0による認証・同期
- **ベクトル検索**: ChromaDBによるセマンティック検索
- **AI研究相談**: RAG + LLMによる研究アドバイス
- **スマート推薦**: 関連性フィルタリングによる精度の高い推薦
- **統計ダッシュボード**: リアルタイムデータ可視化

#### PaaS API
- **開発用API** (paas_api.py): 認証なしHTTP API
- **本番用API** (paas_api_with_auth.py): 認証付きHTTP API
- **RAGインターフェース**: 統合検索・相談機能

#### 並行開発用インターフェース
- **ポート抽象化**: 入力・検索・認証・サービス統合の抽象レイヤー
- **実装クラス**: ChromaDBベクトル検索、Google Drive連携

#### 本番環境対応（実装済み、設定で有効化）
- **PostgreSQL対応**: 本番DBサポート
- **Pinecone対応**: クラウドベクトルDB連携
- **認証機能**: Google OAuth2, JWT
- **セキュリティ**: CORS, Rate Limiting

### 🚧 未実装機能

- **Docker化**: docker-compose.yml, Dockerfile未作成
- **デプロイスクリプト**: Render.comデプロイ自動化
- **データベース移行**: SQLite→PostgreSQL移行スクリプト
- **Looker Studio連携**: データエクスポート機能（ブランチ名のみ存在）

### 📝 テスト状況
- **単体テスト**: agent/tests/ にて一部実装
- **統合テスト**: tests/integration/ にて一部実装
- **カバレッジ**: pytest-covで測定可能
- **注意**: 一部テストが旧データベース構造対象のため要更新

## 主な改善点

### v2.1 - スマート推薦機能 🎯
- **Google Drive直接リンク**: 論文・ポスター・データセットへのワンクリックアクセス
- **関連性フィルタリング**: スコアリングによる精度の高い推薦
  - データセット閾値: スコア5以上（重要キーワード2つ以上一致）
  - stopwords拡張: 一般的すぎる単語を自動除外
- **UI改善**: 各アイテムに「開く」ボタンを表示
- **推薦精度向上**: 関連性の低いアイテムを自動除外

### v2.0 - セマンティック検索RAG 🔍
- **ChromaDB**による高速ベクトル検索
- **sentence-transformers**で意味ベースの検索
- TF-IDFフォールバックのハイブリッド検索
- **PaaS API統合**: 外部システムからHTTP経由で利用可能

### v1.5 - Web OAuth認証 🔐
- サービスアカウント不要、Googleアカウントでログイン
- Web UI上でフォルダ選択
- 認証情報の永続化でリロード対応

### v1.0 - 基本機能 📊
- リアルタイム統計表示
- Chart.jsによる可視化
- データタイプ別分析
- カテゴリー別データベース構造

---

**スマート推薦 + ベクトル検索RAGで、研究データ管理を次のレベルへ！** 🚀
