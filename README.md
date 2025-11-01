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
├── web_app.py                      # メインWebアプリケーション
├── templates/
│   └── index.html                 # フロントエンドUI（TailwindCSS）
├── agent/
│   ├── source/
│   │   ├── integrations/          # クラウド連携機能
│   │   │   ├── vector_search.py   # ベクトル検索エンジン（ChromaDB）
│   │   │   ├── vector_indexer.py  # インデックス作成・管理
│   │   │   └── looker_export.py   # データエクスポート
│   │   ├── database/              # データベース関連
│   │   │   ├── connection.py      # DB接続管理
│   │   │   ├── new_models.py      # データモデル
│   │   │   └── new_repository.py  # リポジトリパターン
│   │   ├── advisor/               # AI相談機能
│   │   │   └── enhanced_research_advisor.py  # RAG + 関連性フィルタリング
│   │   └── analyzer/              # ファイル解析
│   │       └── gemini_client.py   # Gemini API クライアント
│   └── database/
│       └── research_data.db       # SQLiteデータベース
├── chroma_db/                     # ベクトルDB永続化ディレクトリ
├── credentials/                   # 認証情報（.gitignore）
│   ├── google_drive_credentials.json  # OAuth Client ID
│   ├── google_oauth_token.json        # 保存されたトークン
│   └── client_secret.json             # OAuth設定
├── scripts/                       # テスト・デバッグスクリプト
│   ├── check_response.py          # API応答テスト
│   ├── test_sync.py               # Drive同期テスト
│   └── migrate_add_drive_urls.py  # マイグレーションスクリプト
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

### 関連性フィルタリング設定
- **データセット推薦閾値**: スコア5以上（重要キーワード2つ以上一致 or データセット名一致）
- **stopwords**: 一般的すぎる単語を除外（「研究」「分析」「データ」など）
- **推薦精度**: 関連性の高いアイテムのみを表示

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

## ライセンス

研究・教育目的での利用を前提としています。

## 貢献

プルリクエストやイシューの報告を歓迎します。

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

### v1.5 - Web OAuth認証 🔐
- サービスアカウント不要、Googleアカウントでログイン
- Web UI上でフォルダ選択
- 認証情報の永続化でリロード対応

### v1.0 - 基本機能 📊
- リアルタイム統計表示
- Chart.jsによる可視化
- データタイプ別分析

---

**スマート推薦 + ベクトル検索RAGで、研究データ管理を次のレベルへ！** 🚀