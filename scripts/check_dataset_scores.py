import requests
import json

url = "http://localhost:8000/api/consultation"
payload = {
    "query": "LLMのバイアスに関する研究を教えて",
    "consultation_type": "general"
}

response = requests.post(url, json=payload)
data = response.json()

print("=" * 60)
print("データセットの関連性スコア確認")
print("=" * 60)

datasets = data.get('relevant_datasets', [])
print(f"\n表示されたデータセット数: {len(datasets)}")

for i, ds in enumerate(datasets, 1):
    print(f"\n[{i}] {ds.get('name')}")
    print(f"    relevance_score: {ds.get('relevance_score', 'なし')}")
    print(f"    description: {ds.get('description')}")
