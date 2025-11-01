"""
UI表示デバッグ
"""
import requests

print("=" * 70)
print("UI表示デバッグ")
print("=" * 70)

# AI相談APIを呼び出し
print("\n📞 API呼び出し: 「データセットについて教えて」\n")
response = requests.post(
    "http://localhost:8000/api/consultation",
    json={"query": "データセットについて教えて", "consultation_type": "database"},
    timeout=30
)

if response.status_code == 200:
    data = response.json()

    print("✅ APIレスポンス成功\n")
    print(f"アドバイス: {data.get('advice', '')[:100]}...\n")

    # 関連文書チェック
    related_docs = data.get('related_documents', [])
    print(f"📄 related_documents: {len(related_docs)}件")
    if related_docs:
        for doc in related_docs[:2]:
            print(f"   - {doc.get('title', 'N/A')}")

    # 関連データセットチェック
    relevant_datasets = data.get('relevant_datasets', [])
    print(f"\n💾 relevant_datasets: {len(relevant_datasets)}件")
    if relevant_datasets:
        for ds in relevant_datasets[:2]:
            print(f"   - {ds.get('name', 'N/A')}")

    print("\n" + "=" * 70)
    print("JavaScript側の判定")
    print("=" * 70)

    has_related_docs = related_docs and len(related_docs) > 0
    has_relevant_datasets = relevant_datasets and len(relevant_datasets) > 0

    print(f"\nhasRelatedDocs = {has_related_docs}")
    print(f"hasRelevantDatasets = {has_relevant_datasets}")

    if not has_related_docs and not has_relevant_datasets:
        print("\n❌ 問題: どちらも空なので、セクション自体が表示されません")
        print("   → section.classList.add('hidden') が実行されます")
        print("\n原因:")
        print("   - ベクトル検索のインデックスがない")
        print("   - consultation_type が 'database' なので関連文書が検索されない")
    else:
        print("\n✅ セクションは表示されるはずです")

        if has_relevant_datasets:
            print(f"\n💾 データセット {len(relevant_datasets)}件の詳細:")
            for i, ds in enumerate(relevant_datasets[:3], 1):
                print(f"\n  [{i}] {ds.get('name', 'N/A')}")
                print(f"      drive_url: {ds.get('drive_url', 'None')}")

                if ds.get('drive_url'):
                    print(f"      ✅ 「開く」ボタンが表示されます")
                else:
                    print(f"      ❌ 「開く」ボタンは表示されません（drive_url=None）")

    print("\n" + "=" * 70)
    print("ブラウザ確認ポイント")
    print("=" * 70)
    print("""
1. ブラウザの開発者ツールを開く（F12キー）
2. Console タブを確認
   → エラーが出ていないか確認

3. Elements タブで以下を検索:
   id="related-items-section"

   表示されている場合:
   <div id="related-items-section" class="mt-4 p-4 ...">

   表示されていない場合:
   <div id="related-items-section" class="hidden mt-4 p-4 ...">
                                           ^^^^^ hidden がついている

4. もしセクション自体が見つからない場合:
   → ページをリロード（F5）してください
""")

else:
    print(f"❌ APIエラー: {response.status_code}")
    print(response.text)
