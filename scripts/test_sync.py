import requests
import json
import time

print("="*60)
print("Google Drive 同期テスト")
print("="*60)

# 1. 認証状態確認
print("\n1. 認証状態確認...")
auth_response = requests.get("http://localhost:8000/api/auth/google/status")
print(f"Status: {auth_response.status_code}")
auth_data = auth_response.json()
print(f"Authenticated: {auth_data.get('authenticated')}")

if not auth_data.get('authenticated'):
    print("❌ 認証されていません。先にGoogle認証を完了してください。")
    exit(1)

# 2. フォルダ一覧取得
print("\n2. フォルダ一覧取得...")
folders_response = requests.get("http://localhost:8000/api/drive/folders")
print(f"Status: {folders_response.status_code}")
if folders_response.status_code == 200:
    folders_data = folders_response.json()
    print(f"Response: {json.dumps(folders_data, indent=2, ensure_ascii=False)}")

    # folders が dict の場合と list の場合を考慮
    if isinstance(folders_data, dict):
        folders = folders_data.get('folders', [])
    else:
        folders = folders_data

    print(f"フォルダ数: {len(folders)}")

    # "datasets" フォルダを探す
    datasets_folder = None
    for folder in folders:
        if folder['name'] == 'datasets':
            datasets_folder = folder
            break

    if datasets_folder:
        print(f"✅ datasets フォルダ発見: {datasets_folder['name']}")
        folder_id = datasets_folder['id']
        print(f"   ID: {folder_id}")
    else:
        print("❌ datasets フォルダが見つかりません")
        exit(1)
else:
    print(f"エラー: {folders_response.text}")
    exit(1)

# 3. 同期前のデータセット状態確認
print("\n3. 同期前のデータセット状態...")
import sqlite3
conn = sqlite3.connect('agent/database/research_data.db')
cursor = conn.cursor()
cursor.execute("SELECT name, drive_folder_id, drive_url FROM datasets LIMIT 3")
datasets_before = cursor.fetchall()
for name, ds_folder_id, url in datasets_before:
    print(f"  {name}: drive_folder_id={ds_folder_id}, drive_url={url}")
conn.close()

# 4. 同期実行
print("\n4. 同期実行...")
sync_payload = {
    "folder_id": folder_id,
    "folder_type": "all"
}
print(f"Folder ID: {folder_id}")
print(f"Folder Type: all")

sync_response = requests.post(
    "http://localhost:8000/api/sync/google-drive",
    json=sync_payload
)
print(f"Status: {sync_response.status_code}")
if sync_response.status_code == 200:
    sync_result = sync_response.json()
    print(f"Result: {json.dumps(sync_result, indent=2, ensure_ascii=False)}")
else:
    print(f"エラー: {sync_response.text}")
    exit(1)

# 5. 同期後のデータセット状態確認
print("\n5. 同期後のデータセット状態...")
time.sleep(1)  # 少し待つ
conn = sqlite3.connect('agent/database/research_data.db')
cursor = conn.cursor()
cursor.execute("SELECT name, drive_folder_id, drive_url FROM datasets LIMIT 3")
datasets_after = cursor.fetchall()
for name, folder_id, url in datasets_after:
    print(f"  {name}: drive_folder_id={folder_id}, drive_url={url}")
conn.close()

# 6. 変更確認
print("\n6. 変更確認...")
if datasets_before == datasets_after:
    print("❌ データセットに変更がありません！")
    print("\n詳細:")
    print("Before:", datasets_before)
    print("After:", datasets_after)
else:
    print("✅ データセットが更新されました！")
