import requests

response = requests.post(
    "http://localhost:8000/api/consultation",
    json={"query": "ESG投資について教えて", "consultation_type": "general"}
)

data = response.json()
datasets = data.get('relevant_datasets', [])

print("=" * 60)
print("クエリ: ESG投資について教えて")
print("=" * 60)
print(f"\n表示されたデータセット数: {len(datasets)}")

for i, ds in enumerate(datasets, 1):
    print(f"\n[{i}] {ds.get('name')}")
    print(f"    relevance_score: {ds.get('relevance_score', 'なし')}")
