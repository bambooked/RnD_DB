#!/bin/bash

echo "=========================================="
echo "研究データ管理システム セットアップ"
echo "=========================================="
echo ""

# .envファイルのチェック
if [ ! -f .env ]; then
    echo "📝 .envファイルを作成しています..."
    cp .env.example .env
    echo "✅ .envファイルを作成しました"
    echo ""
    echo "⚠️  重要: .envファイルを編集してOPENROUTER_API_KEYを設定してください"
    echo "   APIキーは https://openrouter.ai/ で取得できます"
    echo ""
else
    echo "✅ .envファイルは既に存在します"
    echo ""
fi

# APIキーの確認
if grep -q "your_api_key_here" .env 2>/dev/null; then
    echo "⚠️  警告: OPENROUTER_API_KEYがまだ設定されていません"
    echo "   .envファイルを編集して、APIキーを設定してください"
    echo ""
fi

# データディレクトリの作成
echo "📁 データディレクトリを作成しています..."
mkdir -p agent/database
mkdir -p data/paper
mkdir -p data/poster
mkdir -p data/datasets

echo "✅ データディレクトリを作成しました"
echo ""

# サンプルデータのコピー
if [ -d "sample_data/data" ] && [ ! "$(ls -A data/paper 2>/dev/null)" ]; then
    echo "📦 サンプルデータをコピーしています..."
    cp -r sample_data/data/* data/
    echo "✅ サンプルデータをコピーしました"
    echo "   - Papers: 3件"
    echo "   - Posters: 2件"
    echo "   - Datasets: 6種類"
    echo ""
elif [ "$(ls -A data/paper 2>/dev/null)" ]; then
    echo "ℹ️  データディレクトリには既にファイルが存在します（スキップ）"
    echo ""
fi

# セットアップ完了
echo "=========================================="
echo "✨ セットアップ完了！"
echo "=========================================="
echo ""
echo "次のステップ:"
echo "  1. .envファイルを編集してOPENROUTER_API_KEYを設定"
echo "  2. 以下のコマンドでアプリケーションを起動:"
echo ""
echo "     docker-compose up"
echo ""
echo "  3. ブラウザで http://localhost:8000 にアクセス"
echo ""
