#!/usr/bin/env python3
"""
Find and test OneDrive access through user's sites
"""
import json
import requests

# Load token
with open('backend/onedrive_tokens.json') as f:
    token_data = json.load(f)

token = token_data['access_token']
headers = {"Authorization": f"Bearer {token}"}

print("\n" + "="*70)
print("🔍 Finding OneDrive through Sites...")
print("="*70 + "\n")

# Get user's personal site
print("[1] Getting user info...")
resp = requests.get("https://graph.microsoft.com/v1.0/me", headers=headers)
user = resp.json()
user_id = user.get('id')
print(f"User ID: {user_id}")
print(f"User: {user.get('userPrincipalName')}\n")

# Try direct personal site approach
print("[2] Trying to access personal drive through sites...")

# Method 1: Get user's site collection
print("  a) Getting user's personal site...")
resp = requests.get(f"https://graph.microsoft.com/v1.0/users/{user_id}/drive", headers=headers)
print(f"     Status: {resp.status_code}")
if resp.status_code == 200:
    drive = resp.json()
    print(f"     ✅ Drive found: {drive.get('id')}")
else:
    print(f"     ❌ {resp.status_code}")

# Method 2: List all sites user can access
print("\n  b) Listing user's sites...")
resp = requests.get("https://graph.microsoft.com/v1.0/me/memberOf/microsoft.graph.group?$filter=resourceProvisioningOptions/Any(x:x eq 'Team')", 
                   headers=headers)
print(f"     Status: {resp.status_code}")

# Method 3: Try beta API
print("\n  c) Trying beta API for drive...")
resp = requests.get("https://graph.microsoft.com/beta/me/drive", headers=headers)
print(f"     Status: {resp.status_code}")
if resp.status_code == 200:
    drive = resp.json()
    print(f"     ✅ Drive found: {drive.get('id')}")
    drive_id = drive.get('id')
    
    # Try to create folder
    print("\n[3] Testing folder creation in drive...")
    payload = {
        "name": "TST_FOLDER",
        "folder": {}
    }
    resp = requests.post(f"https://graph.microsoft.com/beta/me/drive/root/children",
                        headers={**headers, "Content-Type": "application/json"},
                        json=payload)
    print(f"     Status: {resp.status_code}")
    if resp.status_code in [200, 201]:
        print(f"     ✅ Folder created successfully!")
    else:
        print(f"     Response: {resp.text[:300]}")
else:
    print(f"     Status: {resp.status_code}")
