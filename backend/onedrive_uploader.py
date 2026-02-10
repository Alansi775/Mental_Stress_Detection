"""
Flask Backend for uploading files to OneDrive using Microsoft Graph API

Features:
- Receive file upload requests from HTML/JavaScript
- Upload files to OneDrive with Resumable Upload support
- Create folder structure: /KFUPM_GSR_Project/V{volunteer_id}/
- Error handling and retry logic
- CORS support for browser requests

Usage:
    python3 onedrive_uploader.py
"""

# Fix for Python 3.14 compatibility: add back pkgutil.get_loader
import pkgutil
import sys
from importlib.util import find_spec
from importlib.machinery import ModuleSpec

if not hasattr(pkgutil, 'get_loader'):
    def get_loader(module_or_name):
        if isinstance(module_or_name, str):
            spec = find_spec(module_or_name)
            return spec.loader if spec else None
        else:
            spec = find_spec(module_or_name.__name__)
            return spec.loader if spec else None
    pkgutil.get_loader = get_loader

from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json
import os
import base64
from datetime import datetime
import msal

app = Flask(__name__)
CORS(app)

# Microsoft Graph settings
TENANT = "consumers"
CLIENT_ID = "04b07795-8ddb-461a-bbee-02f9e1bf7b46"
GRAPH_API_ENDPOINT = "https://graph.microsoft.com/v1.0"

# Token cache file - use absolute path or relative from this file's directory
TOKEN_FILE_NAME = "onedrive_tokens.json"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TOKEN_CACHE_FILE = os.path.join(SCRIPT_DIR, TOKEN_FILE_NAME)

# Resumable Upload settings
CHUNK_SIZE = 327680  # 320 KB per chunk

# Local storage fallback
LOCAL_STORAGE_DIR = os.path.join(SCRIPT_DIR, "..", "uploads")

# Global variables
access_token = None
tokens_data = {}


def ensure_local_storage():
    """Create local storage directory if it doesn't exist"""
    try:
        os.makedirs(LOCAL_STORAGE_DIR, exist_ok=True)
        return LOCAL_STORAGE_DIR
    except Exception as e:
        print(f"Error creating local storage directory: {e}")
        return None


def save_file_locally(volunteer_id, filename, file_data):
    """Save file to local storage as fallback when OneDrive is unavailable"""
    try:
        # Create volunteer folder
        volunteer_dir = os.path.join(LOCAL_STORAGE_DIR, f"V{volunteer_id}")
        os.makedirs(volunteer_dir, exist_ok=True)
        
        # Save file
        file_path = os.path.join(volunteer_dir, filename)
        
        if isinstance(file_data, str):
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(file_data)
        else:
            with open(file_path, 'wb') as f:
                f.write(file_data)
        
        print(f"[LOCAL] File saved locally: {file_path}")
        return True
    except Exception as e:
        print(f"[LOCAL] Error saving file locally: {e}")
        return False


def load_tokens():
    """Load tokens from file"""
    global tokens_data, access_token
    
    if not os.path.exists(TOKEN_CACHE_FILE):
        return False
    
    try:
        with open(TOKEN_CACHE_FILE, "r", encoding="utf-8") as f:
            tokens_data = json.load(f)
        
        access_token = tokens_data.get("access_token")
        if access_token:
            print("✅ Tokens loaded successfully")
            return True
        else:
            return False
    except Exception as e:
        print(f"Error loading tokens: {e}")
        return False


def refresh_access_token():
    """Refresh access token using refresh token"""
    global access_token, tokens_data
    
    refresh_token = tokens_data.get("refresh_token")
    if not refresh_token:
        print("No refresh token available")
        return False
    
    try:
        app_client = msal.PublicClientApplication(CLIENT_ID, authority=f"https://login.microsoftonline.com/{TENANT}")
        
        result = app_client.acquire_token_by_refresh_token(refresh_token, scopes=["Files.ReadWrite", "offline_access"])
        
        if "access_token" not in result:
            print(f"Failed to refresh token: {result.get('error_description')}")
            return False
        
        access_token = result["access_token"]
        tokens_data["access_token"] = access_token
        
        with open(TOKEN_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(tokens_data, f, indent=2)
        
        print("✅ Token refreshed successfully")
        return True
    except Exception as e:
        print(f"Error refreshing token: {e}")
        return False


def ensure_folder_exists(parent_path, folder_name):
    """Create folder if it doesn't exist. Returns folder_id."""
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    try:
        # Build the correct API path
        if parent_path:
            # For nested folders: /me/drive/root:/{parent_path}
            search_url = f"{GRAPH_API_ENDPOINT}/me/drive/root:/{parent_path}/{folder_name}?$select=id,name"
            create_url = f"{GRAPH_API_ENDPOINT}/me/drive/root:/{parent_path}:/children"
        else:
            # For root folder: /me/drive/root
            search_url = f"{GRAPH_API_ENDPOINT}/me/drive/root:/{folder_name}?$select=id,name"
            create_url = f"{GRAPH_API_ENDPOINT}/me/drive/root/children"
        
        print(f"[FOLDER] Searching for {folder_name} at {parent_path or 'root'}")
        response = requests.get(search_url, headers=headers)
        print(f"[FOLDER] Search response: {response.status_code}")
        
        if response.status_code == 200:
            folder_data = response.json()
            folder_id = folder_data.get("id")
            print(f"[FOLDER] Found existing folder {folder_name}: {folder_id}")
            return folder_id
        
        # Create folder if not found (404)
        if response.status_code == 404:
            print(f"[FOLDER] Folder not found, creating {folder_name}")
            payload = {
                "name": folder_name,
                "folder": {},
                "@microsoft.graph.conflictBehavior": "rename"
            }
            
            print(f"[FOLDER] Create URL: {create_url}")
            create_response = requests.post(create_url, headers=headers, json=payload)
            print(f"[FOLDER] Create response: {create_response.status_code}")
            
            if create_response.status_code in [201, 200]:
                folder_data = create_response.json()
                folder_id = folder_data.get("id")
                print(f"[FOLDER] Created folder {folder_name}: {folder_id}")
                return folder_id
            else:
                print(f"[FOLDER] Create failed: {create_response.text}")
                return None
        
        print(f"[FOLDER] Search returned unexpected status: {response.status_code}")
        print(f"[FOLDER] Response: {response.text}")
        return None
    
    except Exception as e:
        print(f"FOLDER CREATION ERROR: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def upload_file_resumable(volunteer_id, filename, file_data, file_size):
    """Upload file using Resumable Upload (for large files)"""
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    try:
        # Create folder structure
        main_folder_id = ensure_folder_exists("", "KFUPM_GSR_Project")
        if not main_folder_id:
            return False
        
        volunteer_folder_name = f"V{volunteer_id}"
        volunteer_folder_path = "KFUPM_GSR_Project"
        
        volunteer_folder_id = ensure_folder_exists(volunteer_folder_path, volunteer_folder_name)
        if not volunteer_folder_id:
            return False
        
        # Create upload session
        upload_session_url = f"{GRAPH_API_ENDPOINT}/me/drive/items/{volunteer_folder_id}:/{filename}:/createUploadSession"
        
        session_payload = {
            "item": {
                "@microsoft.graph.conflictBehavior": "rename",
                "name": filename
            }
        }
        
        session_response = requests.post(upload_session_url, headers=headers, json=session_payload)
        
        if session_response.status_code not in [200, 201]:
            return False
        
        upload_url = session_response.json().get("uploadUrl")
        
        # Upload file in chunks
        bytes_data = file_data.encode() if isinstance(file_data, str) else file_data
        total_size = len(bytes_data) if isinstance(bytes_data, bytes) else file_size
        
        for chunk_start in range(0, total_size, CHUNK_SIZE):
            chunk_end = min(chunk_start + CHUNK_SIZE, total_size)
            chunk = bytes_data[chunk_start:chunk_end]
            
            chunk_headers = {
                "Content-Length": str(len(chunk)),
                "Content-Range": f"bytes {chunk_start}-{chunk_end - 1}/{total_size}"
            }
            
            upload_response = requests.put(upload_url, headers=chunk_headers, data=chunk)
            
            if upload_response.status_code not in [200, 201, 202]:
                return False
        
        return True
    
    except Exception as e:
        print(f"RESUMABLE UPLOAD ERROR: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def upload_file_simple(volunteer_id, filename, file_data):
    """Upload simple file (for small files like CSV)"""
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "text/csv" if filename.endswith(".csv") else "application/octet-stream"
    }
    
    try:
        print(f"[UPLOAD] Starting simple upload: {filename}")
        # Create folder structure
        main_folder_id = ensure_folder_exists("", "KFUPM_GSR_Project")
        if not main_folder_id:
            print(f"[UPLOAD] Failed to create/find main folder")
            return False
        
        print(f"[UPLOAD] Main folder ID: {main_folder_id}")
        volunteer_folder_name = f"V{volunteer_id}"
        volunteer_folder_path = "KFUPM_GSR_Project"
        
        volunteer_folder_id = ensure_folder_exists(volunteer_folder_path, volunteer_folder_name)
        if not volunteer_folder_id:
            print(f"[UPLOAD] Failed to create/find volunteer folder")
            return False
        
        print(f"[UPLOAD] Volunteer folder ID: {volunteer_folder_id}")
        
        # Upload file
        upload_url = f"{GRAPH_API_ENDPOINT}/me/drive/items/{volunteer_folder_id}:/{filename}:/content"
        print(f"[UPLOAD] Upload URL: {upload_url}")
        
        if isinstance(file_data, str):
            file_bytes = file_data.encode()
        else:
            file_bytes = file_data
        
        print(f"[UPLOAD] File size: {len(file_bytes)} bytes")
        upload_response = requests.put(upload_url, headers=headers, data=file_bytes)
        print(f"[UPLOAD] Upload response status: {upload_response.status_code}")
        
        if upload_response.status_code in [200, 201]:
            print(f"[UPLOAD] Upload successful for {filename}")
            return True
        
        print(f"[UPLOAD] Upload failed with status {upload_response.status_code}: {upload_response.text}")
        return False
    
    except Exception as e:
        print(f"SIMPLE UPLOAD ERROR: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


@app.route("/api/upload", methods=["POST"])
def upload():
    """Endpoint for file upload requests - with local storage fallback"""
    global access_token
    
    try:
        data = request.get_json()
        
        volunteer_id = data.get("volunteer_id")
        filename = data.get("filename")
        file_data_b64 = data.get("file_data")
        file_type = data.get("file_type", "csv")
        
        if not all([volunteer_id, filename, file_data_b64]):
            return jsonify({
                "success": False,
                "error": "Missing required fields: volunteer_id, filename, file_data"
            }), 400
        
        try:
            file_data = base64.b64decode(file_data_b64)
        except Exception as e:
            return jsonify({
                "success": False,
                "error": f"Decode error: {str(e)}"
            }), 400
        
        print(f"Upload request: {volunteer_id}/{filename}")
        
        # Try OneDrive upload first if we have a token
        onedrive_success = False
        if access_token:
            print(f"[UPLOAD] Attempting OneDrive upload...")
            try:
                if file_type == "video" or len(file_data) > 4 * 1024 * 1024:
                    onedrive_success = upload_file_resumable(volunteer_id, filename, file_data, len(file_data))
                else:
                    onedrive_success = upload_file_simple(volunteer_id, filename, file_data)
            except Exception as e:
                print(f"[UPLOAD] OneDrive upload exception: {e}")
                onedrive_success = False
        
        # If OneDrive failed, try token refresh and retry
        if not onedrive_success and access_token:
            print(f"[UPLOAD] OneDrive upload failed, attempting token refresh...")
            if refresh_access_token():
                try:
                    if file_type == "video" or len(file_data) > 4 * 1024 * 1024:
                        onedrive_success = upload_file_resumable(volunteer_id, filename, file_data, len(file_data))
                    else:
                        onedrive_success = upload_file_simple(volunteer_id, filename, file_data)
                except Exception as e:
                    print(f"[UPLOAD] OneDrive upload after refresh exception: {e}")
                    onedrive_success = False
        
        # If OneDrive still failed, fall back to local storage
        if not onedrive_success:
            print(f"[UPLOAD] OneDrive unavailable, falling back to local storage...")
            ensure_local_storage()
            local_success = save_file_locally(volunteer_id, filename, file_data)
            
            if local_success:
                return jsonify({
                    "success": True,
                    "message": f"File {filename} saved locally (OneDrive unavailable)",
                    "location": "local",
                    "file": filename,
                    "volunteer_id": volunteer_id
                }), 200
            else:
                return jsonify({
                    "success": False,
                    "error": "Upload to OneDrive and local storage both failed"
                }), 500
        
        # OneDrive upload succeeded
        return jsonify({
            "success": True,
            "message": f"File {filename} uploaded to OneDrive successfully",
            "location": "onedrive",
            "file": filename,
            "volunteer_id": volunteer_id
        }), 200
    
    except Exception as e:
        print(f"UPLOAD ERROR: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Even if there's an exception, try local storage
        try:
            ensure_local_storage()
            save_file_locally(data.get("volunteer_id", "unknown"), 
                            data.get("filename", "unknown"), 
                            file_data if 'file_data' in locals() else b"")
        except:
            pass
        
        return jsonify({
            "success": False,
            "error": f"{type(e).__name__}: {str(e)}"
        }), 500


@app.route("/api/status", methods=["GET"])
def status():
    """Check connection status"""
    try:
        if not access_token:
            return jsonify({
                "connected": False,
                "message": "No access token. Run device_auth.py first"
            }), 401
        
        headers = {"Authorization": f"Bearer {access_token}"}
        test_url = f"{GRAPH_API_ENDPOINT}/me"
        response = requests.get(test_url, headers=headers)
        
        if response.status_code == 200:
            user_data = response.json()
            return jsonify({
                "connected": True,
                "message": "Connected to OneDrive",
                "user": user_data.get("userPrincipalName"),
                "timestamp": datetime.now().isoformat()
            }), 200
        else:
            return jsonify({
                "connected": False,
                "message": f"Connection failed: {response.status_code}"
            }), 401
    
    except Exception as e:
        return jsonify({
            "connected": False,
            "error": str(e)
        }), 500


if __name__ == "__main__":
    load_tokens()
    
    print("Flask server starting on http://localhost:5001")
    print("Waiting for requests...")
    
    app.run(host="0.0.0.0", port=5001, debug=False)
