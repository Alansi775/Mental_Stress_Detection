#!/usr/bin/env python3
"""
Simple OneDrive Authentication Setup
This guides you through the Microsoft Device Code Flow authentication
"""

import sys
import os

# Add the project to path
sys.path.insert(0, '/Users/mackbook/Projects/Mental_Stress_Detection')

def main():
    print("\n" + "="*70)
    print("  🔐 OneDrive Authentication Setup")
    print("="*70)
    print("\nThis script will get your OneDrive access token using Microsoft authentication.")
    print("You'll need to sign in with your Microsoft account.\n")
    
    try:
        import msal
        from backend.device_auth import get_device_code_flow_token, save_tokens
        
        print("Starting authentication flow...\n")
        tokens = get_device_code_flow_token()
        
        if tokens:
            if save_tokens(tokens):
                print("\n" + "="*70)
                print("✅  SUCCESS! Authentication Complete")
                print("="*70)
                print("\nYour tokens have been saved to: onedrive_tokens.json")
                print("You can now upload files to OneDrive automatically!")
                print("\nNext steps:")
                print("1. Run: ./START.sh")
                print("2. Use the web interface to record and monitor")
                print("3. Files will automatically upload to OneDrive")
                print("="*70 + "\n")
                return 0
        else:
            print("\n❌ Authentication failed. Please try again.\n")
            return 1
            
    except Exception as e:
        print(f"\n❌ Error: {str(e)}\n")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
