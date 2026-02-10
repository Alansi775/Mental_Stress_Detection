#!/usr/bin/env python3
"""
Get drive details and find KFUPM_GSR_Project folder
"""
import json
import requests

# Load token
with open('backend/onedrive_tokens.json') as f:
    token_data = json.load(f)

token = token_data['access_token']
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

# Site ID from previous test
SITE_ID = "amuc-my.sharepoint.com,f6be3942-be77-4a18-a5de-3273842e43af,42a618ee-d6ed-43d9-bc6b-72cdf7482c7c"

print("\n" + "="*70)
print("📁 Getting Site Drive Details")
print("="*70 + "\n")

# Get site info
print("[1] Getting site info...")
resp = requests.get(f"https://graph.microsoft.com/v1.0/sites/{SITE_ID}", headers=headers)
print(f"Status: {resp.status_code}")
site_data = resp.json()
if resp.status_code == 200:
    print(f"Site: {site_data.get('displayName')}\n")

# Get drives on site
print("[2] Getting drives...")
resp = requests.get(f"https://graph.microsoft.com/v1.0/sites/{SITE_ID}/drives", headers=headers)
print(f"Status: {resp.status_code}")
if resp.status_code == 200:
    drives = resp.json().get('value', [])
    print(f"Found {len(drives)} drive(s):")
    
    if drives:
        drive_id = drives[0].get('id')
        drive_name = drives[0].get('name')
        print(f"  - {drive_name} (ID: {drive_id[:20]}...)\n")
        
        # List items in root
        print("[3] Listing items in drive root...")
        resp = requests.get(f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root/children", headers=headers)
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            items = resp.json().get('value', [])
            print(f"Found {len(items)} item(s):")
            
            kfupm_folder_id = None
            for item in items:
                item_name = item.get('name')
                print(f"  - {item_name}")
                if item_name == "KFUPM_GSR_Project":
                    kfupm_folder_id = item.get('id')
            
            if kfupm_folder_id:
                print(f"\n✅ KFUPM_GSR_Project folder found! ID: {kfupm_folder_id}\n")
                
                # Test upload
                print("[4] Testing file upload...")
                file_bytes = b"Test content"
                resp = requests.put(
                    f"https://graph.microsoft.com/v1.0/drives/{drive_id}/items/{kfupm_folder_id}:/test.txt:/content",
                    headers={**headers, "Content-Type": "text/plain"},
                    data=file_bytes
                )
                print(f"Status: {resp.status_code}")
                if resp.status_code in [200, 201]:
                    print(f"✅ Upload successful!")
                else:
                    print(f"Response: {resp.text[:200]}")
            else:
                print("❌ KFUPM_GSR_Project folder not found")
        else:
            print(f"Response: {resp.text[:300]}")
else:
    print(f"Response: {resp.text[:300]}")
