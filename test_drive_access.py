#!/usr/bin/env python3
import json
import requests

# Load token
with open('backend/onedrive_tokens.json') as f:
    token_data = json.load(f)

token = token_data['access_token']
headers = {"Authorization": f"Bearer {token}"}

print("Trying different OneDrive access methods...\n")

# Test 1: Try SharePoint personal site API
print("[1] Trying user's SharePoint personal site...")
resp = requests.get("https://graph.microsoft.com/v1.0/me/drives", headers=headers)
print(f"Status: {resp.status_code}")
if resp.status_code == 200:
    drives = resp.json().get('value', [])
    print(f"Found {len(drives)} drives:")
    for drive in drives:
        print(f"  - {drive.get('name')}: {drive.get('id')} (type: {drive.get('driveType')})")
else:
    print(f"Response: {resp.text[:300]}\n")

# Test 2: List available sites
print("\n[2] Listing available sites...")
resp = requests.get("https://graph.microsoft.com/v1.0/me/memberOf", headers=headers)
print(f"Status: {resp.status_code}")
if resp.status_code == 200:
    items = resp.json().get('value', [])
    print(f"Member of {len(items)} items")
    for item in items[:3]:
        print(f"  - {item.get('displayName')} ({item.get('id')})")

# Test 3: Check Sites content
print("\n[3] Checking sites...")
resp = requests.get("https://graph.microsoft.com/v1.0/sites?search=*", headers=headers)
print(f"Status: {resp.status_code}")
if resp.status_code == 200:
    sites = resp.json().get('value', [])
    print(f"Found {len(sites)} sites:")
    for site in sites[:3]:
        print(f"  - {site.get('displayName')}: {site.get('id')}")

# Test 4: Try Graph beta API for OneDrive
print("\n[4] Trying beta API for drive...")
resp = requests.get("https://graph.microsoft.com/beta/me/drive", headers=headers)
print(f"Status: {resp.status_code}")
if resp.status_code == 200:
    print("Beta API works!")
    drive = resp.json()
    print(f"Drive ID: {drive.get('id')}")
    print(f"Drive Type: {drive.get('driveType')}")
else:
    print(f"Response: {resp.text[:300]}")
