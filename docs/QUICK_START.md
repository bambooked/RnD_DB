# クイックスタートガイド

## 3ステップでアプリケーションを起動

### 前提条件
- **Docker & Docker Compose** がインストールされていること
- **LLM APIキー** を取得していること（以下のいずれか）
  - [OpenRouter](https://openrouter.ai/) - 推奨（複数モデルを統一APIで利用）
  - [OpenAI](https://platform.openai.com/api-keys) - GPT-4等を直接利用
  - [Google AI Studio](https://makersuite.google.com/app/apikey) - Gemini利用

---

## ステップ1: リポジトリのクローン

```bash
git clone <repository-url>
cd RnDDB/script
```

---

## ステップ2: セットアップスクリプト実行

```bash
./setup.sh
```

このスクリプトは自動的に以下を実行します：
- `.env`ファイルの作成
- データディレクトリの準備
- サンプルデータのコピー

**重要**: セットアップ後、`.env`ファイルを編集してLLMプロバイダーとAPIキーを設定してください。

```bash
# .envファイルを編集
vim .env

# または、直接追記（OpenRouterの場合）
echo "LLM_PROVIDER=openrouter" >> .env
echo "OPENROUTER_API_KEY=your_api_key_here" >> .env

# OpenAIを使う場合
# echo "LLM_PROVIDER=openai" >> .env
# echo "OPENAI_API_KEY=your_api_key_here" >> .env

# Geminiを使う場合
# echo "LLM_PROVIDER=gemini" >> .env
# echo "GEMINI_API_KEY=your_api_key_here" >> .env
```

---

## ステップ3: Docker Composeで起動

```bash
docker-compose up
```

初回起動時はイメージのビルドに数分かかります。

起動完了後、ブラウザで以下にアクセス：
```
http://localhost:8000
```

---

## 🎉 完了！

以下の機能をすぐに試せます：

### 1. ダッシュボード
- 登録されている論文・ポスター・データセットの統計を表示
- サンプルデータ（論文3件、ポスター2件、データセット6種類）がすでに登録済み

### 2. AI研究相談
- `/chat` ページで研究相談
- 7種類の相談タイプから選択
- RAG検索で関連文献を自動参照

### 3. 研究データ検索
- `/search` ページでセマンティック検索
- 論文・ポスター・データセットを横断検索

### 4. データセット閲覧
- `/datasets` ページでデータセット一覧
- 各データセットの詳細情報を表示

---

## ⚙️ 追加設定（オプション）

### ベクトル検索の有効化

より高度なセマンティック検索を使用する場合：

```bash
# .envに追加
echo "ENABLE_VECTOR_SEARCH=true" >> .env

# コンテナ再起動
docker-compose restart

# インデックス作成
curl -X POST http://localhost:8000/api/vector/index
```

### Google Drive連携

Google Driveと連携する場合は、[Google Cloud Console](https://console.cloud.google.com/)でOAuth 2.0設定が必要です。
詳細は[README.md](README.md)の「Google Drive連携」セクションを参照してください。

---

## 🛑 停止方法

```bash
# 停止
docker-compose down

# データも削除する場合
docker-compose down -v
```

---

## 🐛 トラブルシューティング

### ポートが使用中
```bash
# ポート8000が使用中の場合、docker-compose.ymlを編集
# ports: "8001:8000" に変更
```

### APIキーエラー
```bash
# .envファイルを確認
cat .env | grep OPENROUTER_API_KEY

# APIキーが正しく設定されているか確認
```

### データが表示されない
```bash
# コンテナのログを確認
docker-compose logs -f

# データベースを確認
docker-compose exec app sqlite3 agent/database/research_data.db ".tables"
```

---

## 📚 次のステップ

- [README.md](README.md) で全機能の詳細を確認
- [API_REFERENCE.md](docs/API_REFERENCE.md) でAPIエンドポイントを確認
- 独自の研究データを`data/`ディレクトリに追加

---

**さあ、AI研究相談を始めましょう！** 🚀
