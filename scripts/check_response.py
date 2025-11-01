import requests
import json

response = requests.post(
    "http://localhost:8000/api/consultation",
    json={"query": "AI開発に使えるデータセットはありますか？", "consultation_type": "general"}
)

data = response.json()

print(f"related_documents: {len(data.get('related_documents', []))}件")
print(f"relevant_datasets: {len(data.get('relevant_datasets', []))}件")

docs = data.get('related_documents', [])
if docs:
    print('\n=== Papers/Posters (最初の2件) ===')
    for i, d in enumerate(docs[:2], 1):
        print(f"  [{i}]")
        print(f"    type: {d.get('type', 'MISSING')}")
        print(f"    title: {d.get('title', 'MISSING')}")
        print(f"    file_name: {d.get('file_name', 'MISSING')}")
        print(f"    authors: {d.get('authors', 'MISSING')}")
        print(f"    drive_url: {d.get('drive_url', 'None')}")
        print()

dsets = data.get('relevant_datasets', [])
if dsets:
    print('=== Datasets (最初の2件) ===')
    for i, d in enumerate(dsets[:2], 1):
        print(f"  [{i}]")
        print(f"    name: {d.get('name', 'MISSING')}")
        print(f"    description: {d.get('description', 'MISSING')}")
        print(f"    drive_url: {d.get('drive_url', 'None')}")
        print()
