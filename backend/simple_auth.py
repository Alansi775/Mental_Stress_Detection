#!/usr/bin/env python3
"""
Simplified Device Code Authentication for MSAL
Works with 2FA and geographic restrictions
"""

import msal
import json
import os
from datetime import datetime
import sys

# Configuration
CLIENT_ID = "04b07795-8ddb-461a-bbee-02f9e1bf7b46"
TENANT = "common"
SCOPES = ["https://graph.microsoft.com/.default"]
TOKEN_CACHE_FILE = "onedrive_tokens.json"

def get_device_code_flow():
    """Get tokens using Device Code Flow - simplest and most compatible"""
    
    print("\n" + "="*70)
    print(" OneDrive Authentication - Device Code Flow")
    print("="*70)
    print("\nThis method works with 2FA and geographic restrictions.\n")
    
    try:
        # Create MSAL public client app
        app = msal.PublicClientApplication(
            CLIENT_ID,
            authority=f"https://login.microsoftonline.com/{TENANT}"
        )
        
        # Initiate device flow
        print("Getting device code...\n")
        flow = app.initiate_device_flow(scopes=SCOPES)
        
        if "user_code" not in flow:
            error_msg = flow.get("error_description", flow.get("error", "Unknown error"))
            print(f"❌ Failed to get device code: {error_msg}")
            return None
        
        # Display instructions
        print("="*70)
        print("📱 DEVICE CODE AUTHENTICATION")
        print("="*70)
        print(f"\n  Device Code: {flow['user_code']}")
        print(f"  Verification URL: {flow['verification_uri']}")
        print("\n" + "-"*70)
        print("INSTRUCTIONS:")
        print("-"*70)
        print(f"1. Open browser: {flow['verification_uri']}")
        print(f"2. Enter code: {flow['user_code']}")
        print(f"3. Sign in with: kfupm@almutlaqunited.com")
        print(f"4. Complete 2FA if prompted")
        print(f"5. Confirm permissions")
        print(f"\nCode expires in: {flow.get('expires_in', 900)} seconds")
        print("-"*70 + "\n")
        print("⏳ Waiting for authentication...")
        print("   (Leave this terminal open until authentication completes)\n")
        
        # Wait for user to complete authentication
        result = app.acquire_token_by_device_flow(flow)
        
        if "access_token" not in result:
            error_msg = result.get("error_description", result.get("error", "Unknown error"))
            print(f"\n❌ Authentication failed: {error_msg}")
            return None
        
        print("\n✅ Authentication successful!")
        return result
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def save_tokens(tokens):
    """Save tokens to file"""
    try:
        tokens["timestamp"] = datetime.now().isoformat()
        
        # Determine correct path
        token_path = TOKEN_CACHE_FILE
        if os.path.exists("backend"):
            token_path = f"backend/{TOKEN_CACHE_FILE}"
        
        os.makedirs(os.path.dirname(token_path) if "/" in token_path else ".", exist_ok=True)
        
        with open(token_path, "w", encoding="utf-8") as f:
            json.dump(tokens, f, indent=2)
        
        print(f"✅ Tokens saved to: {os.path.abspath(token_path)}")
        print(f"   Access Token: {tokens['access_token'][:20]}...") 
        print(f"   Refresh Token: {tokens.get('refresh_token', 'N/A')[:20]}...")
        
        return True
    except Exception as e:
        print(f"❌ Error saving tokens: {e}")
        return False

def main():
    """Main authentication flow"""
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*68 + "║")
    print("║" + "  🔐 OneDrive Account Setup for GSR Stress Monitor".center(68) + "║")
    print("║" + " "*68 + "║")
    print("╚" + "="*68 + "╝")
    
    # Get tokens
    tokens = get_device_code_flow()
    
    if not tokens:
        print("\n" + "="*70)
        print("❌ Authentication Failed")
        print("="*70)
        print("\nPlease try again or contact support.")
        print("="*70 + "\n")
        return 1
    
    # Save tokens
    if save_tokens(tokens):
        print("\n" + "="*70)
        print("✅  SUCCESS! Your OneDrive is Connected")
        print("="*70)
        print("\n  📁 Files will upload to:")
        print("     /KFUPM_GSR_Project/V{volunteer_id}/")
        print("\n  🎬 You can now:")
        print("     1. Run: ./START.sh")
        print("     2. Record stress monitoring sessions")
        print("     3. Files auto-upload to your OneDrive")
        print("\n" + "="*70 + "\n")
        return 0
    else:
        print("\n" + "="*70)
        print("❌ Failed to save tokens")
        print("="*70 + "\n")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n❌ Authentication cancelled.")
        sys.exit(1)
