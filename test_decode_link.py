#!/usr/bin/env python3
"""
Try to decode share link and use direct REST upload
"""
import json
import requests
import urllib.parse

# Load token
with open('backend/onedrive_tokens.json') as f:
    token_data = json.load(f)

token = token_data['access_token']

print("\n" + "="*70)
print("🔗 Decode SharePoint Share Link")
print("="*70 + "\n")

# The share link
SHARE_LINK = "https://amuc-my.sharepoint.com/:f:/g/personal/kfupm_almutlaqunited_com/IgDQbs8DtFsXT6QnBtBTEsJeAVc8WAAhxoarPKNGBK0f1Gk?e=18Ob5a"

print(f"Share Link: {SHARE_LINK}\n")

# Method: Use sharing links endpoint
headers = {"Authorization": f"Bearer {token}"}

# Try sharing/get method (Microsoft's way to decode shares)
print("[1] Trying to decode share link...")
payload = {
    "sharing": {
        "sharingLinkInfo": SHARE_LINK
    }
}

resp = requests.post(
    "https://graph.microsoft.com/v1.0/shares/find",
    headers={**headers, "Content-Type": "application/json"},
    json=payload
)
print(f"Status: {resp.status_code}")
print(f"Response: {resp.text[:300]}\n")

# Try alternative: Parse link and extract info
print("[2] Analyzing link structure...")
# Extract the encoded ID from the URL
import re
match = re.search(r'[a-zA-Z0-9_-]+\?', SHARE_LINK)
if match:
    encoded_id = match.group(0)[:-1]
    print(f"Encoded ID found: {encoded_id}\n")
    
    # Try using webUrl parameter
    print("[3] Testing upload using webUrl...")
    
    # Create a structure for API
    web_url_encoded = urllib.parse.quote(SHARE_LINK, safe='')
    
    # Try direct children endpoint with web URL
    print(f"Web URL encoded: {web_url_encoded[:50]}...")
