# 研究データ管理システム - R&D DB

Google Drive連携 & ベクトル検索RAG搭載 AI研究相談システム

## 概要

Google Drive連携とAI（Google Gemini + セマンティック検索）を活用した研究相談機能を備えた、完全なWebベースの研究データ管理システムです。研究者が論文、ポスター、データセットを効率的に管理し、**最新のベクトル検索技術**でリアルタイムにAI相談を受けられます。

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

### 🤖 **AI研究相談（RAG + LLM）**
- **セマンティック検索RAG**: ChromaDB + sentence-transformers による意味理解
- **ハイブリッド検索**: ベクトル検索とTF-IDFの組み合わせ
- **完全LLM駆動**: Google Gemini APIによる動的な研究アドバイス
- **コンテキスト検索**: 既存データベースを参照した的確な助言
- **研究計画支援**: プロジェクト計画から実行まで包括的サポート
- **関連文書提示**: 質問に関連する論文・データセットを自動抽出

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
- **FastAPI**: 高性能WebAPIフレームワーク
- **SQLite**: 軽量データベース
- **Google APIs**: Drive API, Gemini API
- **ChromaDB**: ベクトルデータベース
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
- **JWT**: セッション管理
- **uvicorn**: ASGI サーバー
- **PyTorch**: 機械学習バックエンド（MPS/CUDA対応）

## クイックスタート

### 1. 依存関係のインストール

```bash
# uvを使用（推奨）
uv sync

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
# uvicorn で起動
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

### システム状態
- `GET /api/status` - システム状態確認
- `GET /api/vector/status` - ベクトル検索状態確認

### Google OAuth認証
- `GET /api/auth/google/login` - Google認証開始
- `GET /api/auth/google/callback` - OAuth コールバック
- `GET /api/auth/google/status` - 認証状態確認

### データ同期
- `POST /api/sync/google-drive` - Google Drive同期実行
- `GET /api/drive/folders` - Driveフォルダ一覧取得

### ベクトル検索（新機能）
- `POST /api/vector/index` - 全ドキュメントのインデックス作成
- `POST /api/vector/search` - セマンティック検索実行

### 検索・相談
- `POST /api/search` - 研究データ検索（ハイブリッド）
- `POST /api/consultation` - AI研究相談（RAG対応）

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
├── web_app.py                      # メインWebアプリケーション
├── templates/
│   └── index.html                 # フロントエンドUI
├── agent/source/
│   ├── integrations/              # クラウド連携機能
│   │   ├── vector_search.py       # ベクトル検索エンジン（ChromaDB）
│   │   ├── vector_indexer.py      # インデックス作成・管理
│   │   └── looker_export.py       # データエクスポート
│   ├── database/                  # データベース関連
│   │   ├── connection.py          # DB接続管理
│   │   └── new_repository.py      # リポジトリパターン
│   ├── advisor/                   # AI相談機能
│   │   └── enhanced_research_advisor.py  # RAG対応アドバイザー
│   └── analyzer/                  # ファイル解析
│       └── gemini_client.py       # Gemini API クライアント
├── chroma_db/                     # ベクトルDB永続化ディレクトリ
├── credentials/                   # 認証情報
│   ├── google_drive_credentials.json  # OAuth Client ID
│   └── google_oauth_token.json        # 保存されたトークン
├── .env                          # 環境設定
├── pyproject.toml                # プロジェクト設定（uv）
└── README.md                     # このファイル
```

## 設定オプション

### 基本設定
- `GEMINI_API_KEY`: Google Gemini APIキー（必須）
- `DATABASE_PATH`: SQLiteデータベースパス
- `DATA_DIR_PATH`: ローカルデータディレクトリ

### ベクトル検索設定（新機能）
- `ENABLE_VECTOR_SEARCH`: ベクトル検索有効化（`true`推奨）
- `VECTOR_SEARCH_PROVIDER`: プロバイダー（`chroma`）
- `VECTOR_EMBEDDING_MODEL`: 埋め込みモデル（`sentence-transformers/all-MiniLM-L6-v2`）
- `VECTOR_DIMENSION`: ベクトル次元（`384`）

### Google OAuth設定
- `OAUTH_CLIENT_ID`: OAuth 2.0 クライアントID
- `OAUTH_CLIENT_SECRET`: OAuth 2.0 クライアントシークレット
- `OAUTH_REDIRECT_URI`: リダイレクトURI（`http://localhost:8000/api/auth/google/callback`）

### パフォーマンス設定
- `CHAT_HISTORY_LIMIT`: チャット履歴保持数
- `MAX_RESPONSE_LENGTH`: AI応答最大長
- `SIMILARITY_THRESHOLD`: 検索類似度閾値（ベクトル検索: 0.3-0.5推奨）

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

## ライセンス

研究・教育目的での利用を前提としています。

## 貢献

プルリクエストやイシューの報告を歓迎します。

## 主な改善点（v2.0）

### 🎯 セマンティック検索RAG
- **ChromaDB**による高速ベクトル検索
- **sentence-transformers**で意味ベースの検索
- TF-IDFフォールバックのハイブリッド検索

### 🔐 Web OAuth認証
- サービスアカウント不要、Googleアカウントでログイン
- Web UI上でフォルダ選択
- 認証情報の永続化でリロード対応

### 📊 ダッシュボード強化
- リアルタイム統計表示
- Chart.jsによる可視化
- データタイプ別分析

---

**最新のベクトル検索RAGで、研究データ管理を次のレベルへ！** 🚀