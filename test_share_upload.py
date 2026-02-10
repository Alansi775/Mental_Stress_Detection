#!/usr/bin/env python3
"""
Upload directly using share link format
Microsoft supports uploading to share links directly
"""
import json
import requests
import base64
import urllib.parse

# Load token
with open('backend/onedrive_tokens.json') as f:
    token_data = json.load(f)

token = token_data['access_token']

# The share link for the folder
SHARE_LINK = "https://amuc-my.sharepoint.com/:f:/g/personal/kfupm_almutlaqunited_com/IgDQbs8DtFsXT6QnBtBTEsJeAVc8WAAhxoarPKNGBK0f1Gk?e=18Ob5a"

print("\n" + "="*70)
print("📤 Direct Upload via Microsoft Share Link")
print("="*70 + "\n")

# Microsoft has an undocumented but working endpoint for share links
# Format: https://graph.microsoft.com/v1.0/me/drive/items/root%3Apath%3A/children
# But for shares, we can use: https://graph.microsoft.com/v1.0/shares/{ENCODED_SHARE_URL}

try:
    # Encode share URL for API
    encoded_share = base64.b64encode(SHARE_LINK.encode()).decode().rstrip('=').replace('+', '-').replace('/', '_')
    
    print(f"[1] Using encoded share: {encoded_share[:30]}...\n")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get share metadata
    share_endpoint = f"https://graph.microsoft.com/v1.0/shares/{encoded_share}"
    print(f"[2] Getting share info...")
    resp = requests.get(share_endpoint, headers={**headers, "Accept": "application/json"})
    print(f"Status: {resp.status_code}")
    
    if resp.status_code == 200:
        share_data = resp.json()
        print(f"Share type: {share_data.get('driveItem', {}).get('name')}\n")
        
        # Get the drive item info
        drive_item = share_data.get('driveItem', {})
        if 'id' in drive_item:
            item_id = drive_item['id']
            print(f"Item ID: {item_id}\n")
            
            # Now try to upload to this item (as children)
            print("[3] Uploading test file to folder...")
            
            file_content = b"Test file - uploaded via share link!"
            file_name = "test_via_share.txt"
            
            # Use the driveItem's parent drive reference
            if 'parentReference' in drive_item:
                parent_ref = drive_item['parentReference']
                drive_id = parent_ref.get('driveId')
                
                if drive_id:
                    upload_url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/items/{item_id}:/{file_name}:/content"
                    print(f"Upload URL: {upload_url[:70]}...\n")
                    
                    resp = requests.put(
                        upload_url,
                        headers={**headers, "Content-Type": "text/plain"},
                        data=file_content
                    )
                    print(f"Upload Status: {resp.status_code}")
                    if resp.status_code in [200, 201]:
                        print("✅ Upload successful!")
                        print(f"Response: {json.dumps(resp.json(), indent=2)[:300]}")
                    else:
                        print(f"Error: {resp.text[:300]}")
    else:
        print(f"Share endpoint error: {resp.text[:300]}")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*70)
