#!/usr/bin/env python3
"""
Test uploading to SharePoint folder using the folder URL
"""
import json
import requests
import base64

# Load token
with open('backend/onedrive_tokens.json') as f:
    token_data = json.load(f)

token = token_data['access_token']

# SharePoint folder info
SITE_ID = "amuc-my.sharepoint.com,f6be3942-be77-4a18-a5de-3273842e43af,42a618ee-d6ed-43d9-bc6b-72cdf7482c7c"
FOLDER_ID = "IgDQbs8DtFsXT6QnBtBTEsJeAVc8WAAhxoarPKNGBK0f1Gk"

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

print("\n" + "="*70)
print("📤 Testing Direct Upload to SharePoint Folder")
print("="*70 + "\n")

# Test 1: Try to get folder info
print("[1] Getting folder info...")
resp = requests.get(
    f"https://graph.microsoft.com/v1.0/sites/{SITE_ID}/drive/items/{FOLDER_ID}",
    headers=headers
)
print(f"Status: {resp.status_code}")
if resp.status_code == 200:
    folder = resp.json()
    print(f"✅ Folder found: {folder.get('name')}\n")
else:
    print(f"Response: {resp.text[:200]}\n")

# Test 2: Upload a test file
print("[2] Uploading test file...")
file_name = "test_upload.txt"
file_content = "Test data - if you see this, upload worked!"
file_bytes = file_content.encode('utf-8')

upload_headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "text/plain"
}

upload_url = f"https://graph.microsoft.com/v1.0/sites/{SITE_ID}/drive/items/{FOLDER_ID}:/{file_name}:/content"

resp = requests.put(upload_url, headers=upload_headers, data=file_bytes)
print(f"Status: {resp.status_code}")

if resp.status_code in [200, 201]:
    print(f"✅ File uploaded successfully!")
    file_info = resp.json()
    print(f"File ID: {file_info.get('id')}")
else:
    print(f"Response: {resp.text[:300]}")

print("\n" + "="*70)
