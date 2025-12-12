# デモの始め方

このアプリケーションは研究データを管理して、AIに相談できるシステムです。
サンプルデータが既に入っているので、すぐに試せるように設計してあります。

## 環境変数の設定

まず、.env.demoをコピーして.envファイルを作ります。

```bash
cp .env.demo .env
```

.envファイルを開いて、最低限以下の2つを設定してください。

**必須の設定**

```env
# 使いたいLLMプロバイダーを選ぶ（openrouter, openai, gemini のいずれか）
LLM_PROVIDER=openrouter

# 選んだプロバイダーのAPIキーを設定
OPENROUTER_API_KEY=your_openrouter_api_key_here
```

その他の設定（データベースパス、ポート番号、Google Drive連携など）は、
必要に応じて変更してください。デフォルトのままでも動くようにはしてあります。

## アプリケーションの起動

環境変数を設定したら、Dockerで起動します。

```bash
docker-compose up
```

ブラウザで http://localhost:8000 を開けば、すぐに使えます。
論文11件、ポスター4件、データセット10個が入っています。

## 何ができるか試してみる

トップページから以下のことができます。

- データベースサマリー：どんなデータが入っているか見る
- 研究データ検索：キーワードで論文やデータセットを探す
- AI研究相談：研究の進め方をAIに相談する（APIキーが必要）
- ベクトル検索：意味が似ている文書を探す

Google Driveと連携すれば、自分のデータも取り込めます。
その場合は、Google Cloud Consoleで認証情報を取得して、credentials/ディレクトリに保存してください。

## 困ったとき

データベースの中身を確認したいときは、こうすると見られます。

```bash
sqlite3 agent/database/research_data.db ".tables"
```

論文が何件入っているか確認するなら、こんな感じです。

```bash
sqlite3 agent/database/research_data.db "SELECT COUNT(*) FROM papers;"
```