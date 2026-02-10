"""
Microsoft Graph API authentication using Device Code Flow

This script obtains a refresh token for OneDrive access.

Usage:
    python3 device_auth.py

After running, device codes will be displayed for OneDrive authentication.
"""

import msal
import json
import os
from datetime import datetime

# Application ID - using Microsoft Office public client ID for personal accounts
# Or create your own app in Azure Portal
CLIENT_ID = "04b07795-8ddb-461a-bbee-02f9e1bf7b46"
TENANT = "consumers"
SCOPES = ["https://graph.microsoft.com/.default"]

# Path where tokens will be saved
TOKEN_CACHE_FILE = "onedrive_tokens.json"


def get_device_code_flow_token():
    """
    Get tokens using Device Code Flow
    Displays device code and verification URL for user authentication
    """
    print("=" * 60)
    print("🔐 Microsoft OneDrive - Device Code Authentication")
    print("=" * 60)
    
    # Create MSAL application
    app = msal.PublicClientApplication(CLIENT_ID, authority=f"https://login.microsoftonline.com/{TENANT}")
    
    # Get device code
    flow = app.initiate_device_flow(scopes=SCOPES)
    if "user_code" not in flow:
        print("Error obtaining device code")
        print(flow.get("error_description", flow.get("error")))
        return None
    
    # Display device code and verification URL
    print(f"\nDevice Code: {flow['user_code']}")
    print(f"Verification URL: {flow['verification_uri']}")
    print("\nPlease navigate to the URL above and enter the device code...")
    print(f"Code expires in {flow.get('expires_in', 900)} seconds\n")
    
    # Wait for user authentication
    result = app.acquire_token_by_device_flow(flow)
    
    if "access_token" not in result:
        print("Authentication failed")
        print(result.get("error_description", result.get("error")))
        return None
    
    return result


def save_tokens(tokens):
    """
    Save tokens to JSON file
    """
    try:
        # Add current timestamp
        tokens["timestamp"] = datetime.now().isoformat()
        
        with open(TOKEN_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(tokens, f, indent=2, ensure_ascii=False)
        
        print(f"\nTokens saved to: {TOKEN_CACHE_FILE}")
        print(f"Access Token: {tokens['access_token'][:30]}...")
        print(f"Refresh Token: {tokens['refresh_token'][:30]}...")
        
        return True
    except Exception as e:
        print(f"Error saving tokens: {e}")
        return False


def load_tokens():
    """
    Load tokens from file
    """
    if not os.path.exists(TOKEN_CACHE_FILE):
        print(f"File not found: {TOKEN_CACHE_FILE}")
        return None
    
    try:
        with open(TOKEN_CACHE_FILE, "r", encoding="utf-8") as f:
            tokens = json.load(f)
        print(f"Tokens loaded from: {TOKEN_CACHE_FILE}")
        return tokens
    except Exception as e:
        print(f"Error loading tokens: {e}")
        return None


def refresh_access_token(refresh_token):
    """
    Refresh access token using refresh token
    """
    try:
        app = msal.PublicClientApplication(CLIENT_ID, authority=f"https://login.microsoftonline.com/{TENANT}")
        
        result = app.acquire_token_by_refresh_token(refresh_token, scopes=SCOPES)
        
        if "access_token" not in result:
            print("Failed to refresh token")
            return None
        
        print("Access token refreshed successfully")
        return result
    except Exception as e:
        print(f"Error refreshing token: {e}")
        return None


def main():
    """
    Main program
    """
    print("\n1. Load existing tokens (if available)")
    print("2. Authenticate using Device Code Flow\n")
    
    choice = input("Choose option (1 or 2): ").strip()
    
    if choice == "1":
        tokens = load_tokens()
        if tokens:
            print("\nExisting tokens:")
            print(f"   - Timestamp: {tokens.get('timestamp', 'Unknown')}")
            print(f"   - Token Type: {tokens.get('token_type', 'N/A')}")
    elif choice == "2":
        tokens = get_device_code_flow_token()
        if tokens:
            save_tokens(tokens)
    else:
        print("Invalid selection")


if __name__ == "__main__":
    main()
