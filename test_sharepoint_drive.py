#!/usr/bin/env python3
"""
Access OneDrive through SharePoint Site
"""
import json
import requests

# Load token
with open('backend/onedrive_tokens.json') as f:
    token_data = json.load(f)

token = token_data['access_token']
headers = {"Authorization": f"Bearer {token}"}

print("\n" + "="*70)
print("🔍 Finding OneDrive via SharePoint Site...")
print("="*70 + "\n")

# Get user info first
print("[1] User info...")
resp = requests.get("https://graph.microsoft.com/v1.0/me", headers=headers)
user = resp.json()
upn = user.get('userPrincipalName')
print(f"User: {upn}\n")

# Try to get site by name pattern (SharePoint personal sites follow pattern)
# For amuc-my.sharepoint.com, personal sites are /personal/username
print("[2] Getting SharePoint personal site...")
site_url_pattern = upn.replace('@', '_').replace('.', '_')
test_url = f"https://graph.microsoft.com/v1.0/sites/amuc-my.sharepoint.com:/personal/{site_url_pattern}"

resp = requests.get(test_url, headers=headers)
print(f"Status: {resp.status_code}")

if resp.status_code == 200:
    site = resp.json()
    site_id = site.get('id')
    print(f"✅ Site found: {site_id}\n")
    
    # Get drive from site
    print("[3] Getting drive from site...")
    drive_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drive"
    resp = requests.get(drive_url, headers=headers)
    print(f"Status: {resp.status_code}")
    
    if resp.status_code == 200:
        drive = resp.json()
        drive_id = drive.get('id')
        print(f"✅ Drive found: {drive_id}\n")
        
        # Try to create folder
        print("[4] Testing folder creation...")
        create_url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root/children"
        payload = {
            "name": "KFUPM_GSR_Project",
            "folder": {}
        }
        resp = requests.post(create_url, 
                            headers={**headers, "Content-Type": "application/json"},
                            json=payload)
        print(f"Status: {resp.status_code}")
        
        if resp.status_code in [200, 201]:
            folder = resp.json()
            print(f"✅ Folder created: {folder.get('id')}")
            print(f"✅ SUCCESS - OneDrive is accessible!\n")
        else:
            print(f"Folder creation response: {resp.text[:300]}")
    else:
        print(f"Drive response: {resp.text[:300]}")
else:
    print(f"Site response: {resp.text[:300]}")
    
    # Try alternative format
    print("\n[2b] Trying alternative site format...")
    alt_url = f"https://graph.microsoft.com/v1.0/sites/amuc-my.sharepoint.com:/personal/{site_url_pattern}:/drive"
    resp = requests.get(alt_url, headers=headers)
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        print("✅ Alternative format works!")
