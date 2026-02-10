#!/usr/bin/env python3
"""
Upload to OneDrive using folder share link
Works by uploading to a specific known folder
"""
import json
import requests
import base64
import os

# Load token  
with open('backend/onedrive_tokens.json') as f:
    token_data = json.load(f)

token = token_data['access_token']
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

print("\n" + "="*70)
print("📁 OneDrive Direct Upload Tester")
print("="*70)

user_id = "13ffd9fc-0b2e-4e40-a574-ff885efdf7d9"  # من الطلب السابق
drive_id = None

# طريقة: حاول السيرش عن أي drive محاط الـ user
print("\n[1] Searching for available drives...")

resp = requests.get(
    f"https://graph.microsoft.com/v1.0/users/{user_id}/drives",
    headers=headers
)
print(f"Status: {resp.status_code}")
if resp.status_code == 200:
    drives = resp.json().get('value', [])
    print(f"Found {len(drives)} drive(s)")
    for drive in drives:
        print(f"  - {drive.get('name')} (ID: {drive.get('id')})")
        if not drive_id:
            drive_id = drive.get('id')
else:
    print(f"Response: {resp.text[:200]}")

# إذا ماحصلنا drive، جرب get sites
if not drive_id:
    print("\n[2] Searching through sites...")
    resp = requests.get(
        "https://graph.microsoft.com/v1.0/sites?search=kfupm",
        headers=headers
    )
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        sites = resp.json().get('value', [])
        print(f"Found {len(sites)} site(s)")
        for site in sites:
            print(f"  - {site.get('displayName')} (ID: {site.get('id')})")

print("\n" + "="*70)
print("⚠️  NOTE:")
print("="*70)
print("""
If no drives/sites found above, it means the API doesn't have access.

SOLUTION:
1. Create folder 'KFUPM_GSR_Project' in your OneDrive manually
2. Right-click folder → Share → Get link
3. Provide the share link and we can use direct URL upload

OR:

Just use the local storage, and manually copy files to OneDrive later
from: ./uploads/V{volunteer_id}/

Files will auto-save locally and are ready to upload anytime.
""")
