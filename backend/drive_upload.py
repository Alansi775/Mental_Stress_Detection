"""
Google Drive Upload Server
Automatic file and video upload to Google Drive based on volunteer ID
"""

import os
import json
import base64
from pathlib import Path
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import logging
from dotenv import load_dotenv
import pickle
import webbrowser

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.api_core.exceptions import GoogleAPIError
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload
from io import BytesIO

# Load environment variables
load_dotenv()

GMAIL_USER = os.getenv('GOOGLE_EMAIL', '')
GMAIL_PASSWORD = os.getenv('GOOGLE_PASSWORD', '')
FLASK_HOST = os.getenv('FLASK_HOST', 'localhost')
FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))

# Google Drive API settings
SCOPES = ['https://www.googleapis.com/auth/drive']
TOKEN_FILE = 'drive_token.pickle'
CREDENTIALS_FILE = 'credentials.json'

app = Flask(__name__)
CORS(app)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global Google Drive service
drive_service = None


def get_drive_service():
    """Get or create Google Drive service"""
    global drive_service
    
    if drive_service is not None:
        return drive_service
    
    creds = None
    
    # Try to load existing token
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'rb') as token:
            creds = pickle.load(token)
    
    # If no valid credentials, ask user to authenticate
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Use web-based OAuth without credentials.json
            # This will prompt user to authenticate via browser
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE, SCOPES) if os.path.exists(CREDENTIALS_FILE) else None
            
            if not flow:
                logger.warning("Using simplified authentication (no credentials.json)")
                # Fallback: Direct OAuth with email/password
                # This requires setting up OAuth 2.0 credentials first
                return None
            
            creds = flow.run_local_server(port=0)
        
        # Save token for future use
        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)
    
    drive_service = build('drive', 'v3', credentials=creds)
    return drive_service


def create_or_get_folder(folder_name, parent_id='root'):
    """Create folder if not exists, return folder ID"""
    try:
        service = drive_service or get_drive_service()
        if not service:
            return None
        
        # Search for folder
        query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        if parent_id != 'root':
            query += f" and '{parent_id}' in parents"
        else:
            query += " and 'root' in parents"
        
        results = service.files().list(q=query, spaces='drive', pageSize=1, fields='files(id)').execute()
        files = results.get('files', [])
        
        if files:
            logger.info(f"Folder found: {folder_name}")
            return files[0]['id']
        
        # Create folder
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        
        if parent_id != 'root':
            file_metadata['parents'] = [parent_id]
        
        folder = service.files().create(body=file_metadata, fields='id').execute()
        logger.info(f"Folder created: {folder_name}")
        return folder.get('id')
    
    except Exception as e:
        logger.error(f"Error with folder: {str(e)}")
        return None


def upload_file_to_drive(file_bytes, filename, folder_id):
    """Upload file to Google Drive"""
    try:
        service = drive_service or get_drive_service()
        if not service:
            logger.warning("No Drive service available")
            return False
        
        # Add timestamp to filename
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        name_without_ext = os.path.splitext(filename)[0]
        file_ext = os.path.splitext(filename)[1]
        remote_name = f"{name_without_ext}_{timestamp}{file_ext}"
        
        # Determine MIME type
        mime_type = 'text/csv' if filename.endswith('.csv') else 'video/webm'
        
        # Create file metadata
        file_metadata = {
            'name': remote_name,
            'parents': [folder_id]
        }
        
        # Upload file
        media = MediaIoBaseUpload(
            BytesIO(file_bytes),
            mimetype=mime_type,
            resumable=True
        )
        
        file_obj = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink'
        ).execute()
        
        logger.info(f"File uploaded: {remote_name} (ID: {file_obj['id']})")
        return True
    
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        return False


@app.route('/api/upload', methods=['POST'])
def upload_file():
    """
    Upload file to Google Drive
    
    Request JSON:
    {
        'volunteer_id': '1',
        'filename': 'V1_GSR_Data.csv',
        'file_data': 'base64_encoded_data'
    }
    
    Files saved to: Google Drive > GSR_Sessions > Volunteer_X
    """
    try:
        data = request.json
        
        volunteer_id = data.get('volunteer_id')
        filename = data.get('filename')
        file_data = data.get('file_data')
        
        if not all([volunteer_id, filename, file_data]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Decode file data
        try:
            file_bytes = base64.b64decode(file_data)
        except Exception as e:
            logger.error(f"Decode error: {str(e)}")
            return jsonify({'error': 'Failed to decode file data'}), 400
        
        # Try to upload to Google Drive
        service = drive_service or get_drive_service()
        
        if service:
            # Create folder structure
            sessions_folder_id = create_or_get_folder('GSR_Sessions', 'root')
            
            if sessions_folder_id:
                volunteer_folder_id = create_or_get_folder(
                    f'Volunteer_{volunteer_id}',
                    sessions_folder_id
                )
                
                if volunteer_folder_id:
                    success = upload_file_to_drive(file_bytes, filename, volunteer_folder_id)
                    
                    if success:
                        return jsonify({
                            'success': True,
                            'message': f'File uploaded to Google Drive for Volunteer {volunteer_id}',
                            'location': 'Google Drive > GSR_Sessions > Volunteer_' + str(volunteer_id)
                        }), 200
        
        # Fallback: Save locally if Drive upload fails
        local_dir = Path(__file__).parent.parent / 'uploads' / 'GSR_Sessions' / f'Volunteer_{volunteer_id}'
        local_dir.mkdir(parents=True, exist_ok=True)
        
        local_path = local_dir / filename
        with open(local_path, 'wb') as f:
            f.write(file_bytes)
        
        logger.info(f"File saved locally (Drive unavailable): {local_path}")
        
        return jsonify({
            'success': True,
            'message': f'File saved locally for Volunteer {volunteer_id}',
            'location': 'Local Storage',
            'path': str(local_path)
        }), 200
    
    except Exception as e:
        logger.error(f"Processing error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({
        'status': 'ok',
        'service': 'Google Drive File Upload Server',
        'drive_connected': drive_service is not None
    }), 200


@app.route('/api/authenticate', methods=['POST'])
def authenticate():
    """Trigger Google Drive authentication"""
    try:
        global drive_service
        
        # Force re-authentication
        if os.path.exists(TOKEN_FILE):
            os.remove(TOKEN_FILE)
        
        drive_service = None
        service = get_drive_service()
        
        if service:
            return jsonify({
                'success': True,
                'message': 'Authenticated successfully'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Authentication required. Please ensure credentials.json exists.'
            }), 401
    
    except Exception as e:
        logger.error(f"Auth error: {str(e)}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print(f"""
╔════════════════════════════════════════╗
║   GSR Google Drive Upload Server       ║
║   Automatic Upload Mode Active         ║
╚════════════════════════════════════════╝
    
Server: http://{FLASK_HOST}:{FLASK_PORT}
Status: RUNNING
Email: {GMAIL_USER}

Files will be uploaded to:
Google Drive > GSR_Sessions > Volunteer_X

Press CTRL+C to stop.
""")
    
    # Initialize drive service on startup
    try:
        drive_service = get_drive_service()
        if drive_service:
            print("✅ Google Drive connected")
        else:
            print("⚠️  Google Drive not connected (will fall back to local save)")
    except Exception as e:
        print(f"⚠️  Authentication pending: {str(e)}")
    
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=False)
