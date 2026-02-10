#!/usr/bin/env python3
"""
Quick OneDrive authentication using Device Code Flow
Run this once to authenticate and save tokens for uploads
"""

import sys
sys.path.insert(0, '/Users/mackbook/Projects/Mental_Stress_Detection')

from backend.device_auth import get_device_code_flow_token, save_tokens

print("\n" + "="*60)
print("OneDrive Authentication - Device Code Flow")
print("="*60 + "\n")

# Get tokens using Device Code Flow
tokens = get_device_code_flow_token()

if tokens:
    save_tokens(tokens)
    print("\n✅ Authentication successful!")
    print("You can now use the system to upload files to OneDrive.")
else:
    print("\n❌ Authentication failed!")
    sys.exit(1)
