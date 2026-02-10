#!/usr/bin/env python3
import json
import requests
import sys

# Load token
with open('backend/onedrive_tokens.json') as f:
    token_data = json.load(f)

token = token_data['access_token']
headers = {"Authorization": f"Bearer {token}"}

# Test 1: Get user info
print("[1] Getting user info...")
resp = requests.get("https://graph.microsoft.com/v1.0/me", headers=headers)
print(f"Status: {resp.status_code}")
if resp.status_code == 200:
    user = resp.json()
    print(f"User: {user.get('userPrincipalName')}\n")
else:
    print(f"Error: {resp.text}\n")

# Test 2: Get drive info
print("[2] Getting drive info...")
resp = requests.get("https://graph.microsoft.com/v1.0/me/drive", headers=headers)
print(f"Status: {resp.status_code}")
if resp.status_code == 200:
    drive_data = resp.json()
    print(f"Drive ID: {drive_data.get('id')}")
    print(f"Drive Type: {drive_data.get('driveType')}\n")
else:
    print(f"Error: {resp.text[:200]}\n")

# Test 3: Get drive root
print("[3] Getting drive root...")
resp = requests.get("https://graph.microsoft.com/v1.0/me/drive/root", headers=headers)
print(f"Status: {resp.status_code}")
if resp.status_code == 200:
    root_data = resp.json()
    print(f"Root ID: {root_data.get('id')}")
    print(f"Root Name: {root_data.get('name')}\n")
else:
    print(f"Error: {resp.text[:200]}\n")

# Test 4: Try to create a test folder in root
print("[4] Attempting to create folder in root...")
payload = {
    "name": "TEST_FOLDER_DELETE_ME",
    "folder": {},
    "@microsoft.graph.conflictBehavior": "replace"
}
resp = requests.post("https://graph.microsoft.com/v1.0/me/drive/root/children", 
                    headers={**headers, "Content-Type": "application/json"},
                    json=payload)
print(f"Status: {resp.status_code}")
print(f"Response: {json.dumps(resp.json(), indent=2)}\n")
