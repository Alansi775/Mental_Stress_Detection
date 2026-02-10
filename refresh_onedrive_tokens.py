#!/usr/bin/env python3
"""
Refresh OneDrive tokens with explicit Files.ReadWrite scope
"""
import msal
import json

CLIENT_ID = "04b07795-8ddb-461a-bbee-02f9e1bf7b46"
TENANT = "common"

# More specific scopes for OneDrive
# Note: Don't include openid, profile, offline_access in refresh request
SCOPES = [
    "https://graph.microsoft.com/Files.ReadWrite",
    "https://graph.microsoft.com/Files.ReadWrite.All"
]

def refresh_tokens():
    """Refresh tokens with OneDrive-specific scopes"""
    
    print("\n" + "="*70)
    print("  🔄 Refreshing OneDrive Tokens with Explicit Scopes")
    print("="*70 + "\n")
    
    # Load existing tokens
    with open('backend/onedrive_tokens.json', 'r') as f:
        existing_tokens = json.load(f)
    
    refresh_token = existing_tokens.get('refresh_token')
    
    if not refresh_token:
        print("❌ No refresh token found!")
        return
    
    try:
        app = msal.PublicClientApplication(CLIENT_ID, authority=f"https://login.microsoftonline.com/{TENANT}")
        
        print(f"Refreshing with scopes:")
        for scope in SCOPES:
            print(f"  - {scope}")
        print()
        
        result = app.acquire_token_by_refresh_token(refresh_token, scopes=SCOPES)
        
        if "access_token" in result:
            print("✅ Token refreshed successfully!")
            
            # Save new tokens
            with open('backend/onedrive_tokens.json', 'w') as f:
                json.dump(result, f, indent=2)
            
            print("\n📝 Updated tokens saved")
            print(f"User: {result.get('scope', '').split()[0]}")
            return True
        else:
            error = result.get('error_description', result.get('error'))
            print(f"❌ Failed: {error}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    refresh_tokens()
