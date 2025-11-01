import requests
import json

url = "http://localhost:8000/api/consultation"
payload = {
    "query": "LLMのバイアスに関する研究を教えて",
    "consultation_type": "general"
}

response = requests.post(url, json=payload)
data = response.json()

print("="*60)
print("APIレスポンス構造")
print("="*60)
print(f"\nStatus: {response.status_code}")
print(f"\nレスポンスキー: {list(data.keys())}")

print(f"\n[related_documents]")
if 'related_documents' in data:
    print(f"  型: {type(data['related_documents'])}")
    print(f"  件数: {len(data['related_documents']) if data['related_documents'] else 0}")
    print(f"  値: {data['related_documents']}")
else:
    print("  ❌ キーが存在しない")

print(f"\n[relevant_datasets]")
if 'relevant_datasets' in data:
    print(f"  型: {type(data['relevant_datasets'])}")
    print(f"  件数: {len(data['relevant_datasets']) if data['relevant_datasets'] else 0}")
    if data['relevant_datasets']:
        print(f"  最初の要素: {data['relevant_datasets'][0]}")
else:
    print("  ❌ キーが存在しない")

print(f"\n完全なレスポンス:")
print(json.dumps(data, indent=2, ensure_ascii=False))
