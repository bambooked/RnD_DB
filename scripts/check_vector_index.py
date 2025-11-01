import chromadb
from chromadb.config import Settings

# ChromaDB クライアント初期化
client = chromadb.PersistentClient(
    path="chroma_db",
    settings=Settings(anonymized_telemetry=False)
)

# コレクション一覧
print("📚 ChromaDB コレクション一覧:")
collections = client.list_collections()
for col in collections:
    print(f"   - {col.name}")

print()

# research_documents コレクション取得
try:
    collection = client.get_collection("research_documents")
    print(f"✅ research_documents コレクション存在")
    print(f"   登録件数: {collection.count()}件")

    # サンプルデータ取得
    if collection.count() > 0:
        results = collection.get(limit=5, include=["metadatas"])
        print(f"\n📄 サンプルドキュメント:")
        for i, (doc_id, metadata) in enumerate(zip(results['ids'], results['metadatas']), 1):
            print(f"   [{i}] ID: {doc_id}")
            print(f"       Type: {metadata.get('type', 'N/A')}")
            print(f"       Title/Name: {metadata.get('title') or metadata.get('name', 'N/A')}")
            print()
    else:
        print("⚠️  コレクションは空です（ドキュメントが登録されていません）")
except Exception as e:
    print(f"❌ research_documents コレクション取得エラー: {e}")
