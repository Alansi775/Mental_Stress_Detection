# GSR Stress Detection System - Setup & Status

## System Overview

The GSR (Galvanic Skin Response) Stress Detection System is a web-based application for monitoring and recording physiological stress responses. It captures real-time GSR data, video recordings, and uploads them for analysis.

### Technology Stack
- **Backend**: Flask 3.1.2 (Python 3.14) on port 5001
- **Frontend**: HTML5 + JavaScript on port 8000
- **Authentication**: Microsoft Azure AD (Device Code Flow)
- **Data Storage**: Local file system (OneDrive unavailable for this account)
- **Data Format**: CSV (GSR measurements), WebM (video recordings)

---

## Quick Start

### Start the System
```bash
./START.sh
```

This starts:
- Flask API server on http://localhost:5001
- HTTP UI server on http://localhost:8000

The UI will be accessible at: **http://localhost:8000/index.html**

### Stop the System
```bash
./STOP.sh
```

---

## System Features

### Data Capture
- **Real-time GSR monitoring** with live graph visualization
- **Multi-stage recording**: Calibration → Normal → Stress → Relaxation
- **Camera integration**: Records volunteer during session
- **Automatic data export**: CSV + WebM video

### File Management
- **Local Storage Path**: `./uploads/V{volunteer_id}/`
  - Files are automatically organized by volunteer ID
  - Format: `V1/`, `V2/`, `V7/`, etc.
- **Automatic File Upload**: Data saved as session ends

### Authentication
- **Microsoft Work Account**: kfupm@almutlaqunited.com
- **Status**: ✅ Authenticated (Device Code Flow)
- **Scopes**: Full Graph API access including Files.ReadWrite

---

## Important Notice: OneDrive Availability

### Current Status
The user's Work/School account doesn't have OneDrive provisioned at the organizational level. This is common for:
- Organizational accounts with restricted cloud storage policies
- Accounts that haven't had OneDrive initialized
- Accounts in organizations using SharePoint instead

### System Behavior
The system now handles this gracefully:

1. **First attempt**: Tries to upload to OneDrive
2. **If OneDrive unavailable**: Automatically falls back to local storage
3. **File locations**: `./uploads/V{volunteer_id}/` on the local machine

### API Response
Successful uploads return:
```json
{
  "success": true,
  "location": "local",
  "message": "File test_data.csv saved locally (OneDrive unavailable)",
  "volunteer_id": "7",
  "file": "test_data.csv"
}
```

---

## File Organization

```
Mental_Stress_Detection/
├── uploads/                          # Local file storage (fallback)
│   ├── V1/                          # Volunteer 1 files
│   │   ├── GSR_Data_*.csv           # GSR measurements
│   │   └── GSR_Recording_*.webm     # Video recordings
│   ├── V7/                          # Volunteer 7 files
│   └── ...
├── backend/
│   ├── onedrive_uploader.py         # Flask API (main server)
│   ├── simple_auth.py               # Device Code authentication
│   ├── onedrive_tokens.json         # OAuth tokens (local)
│   └── requirements.txt
├── ui/
│   └── index.html                   # Web UI
├── START.sh                         # Start system
└── STOP.sh                         # Stop system
```

---

## API Endpoints

### GET /api/status
Check authentication status
```bash
curl http://localhost:5001/api/status
```

Response:
```json
{
  "connected": true,
  "message": "Connected to OneDrive",
  "user": "kfupm@almutlaqunited.com",
  "timestamp": "2026-02-09T16:16:20.304180"
}
```

### POST /api/upload
Upload file with base64-encoded data
```bash
curl -X POST http://localhost:5001/api/upload \
  -H "Content-Type: application/json" \
  -d '{
    "volunteer_id": "7",
    "filename": "GSR_Data.csv",
    "file_data": "<base64-encoded-file>",
    "file_type": "csv"
  }'
```

---

## Recent Changes

### Upload System Update (Feb 9, 2026)
- ✅ Added detailed error logging for debugging
- ✅ Implemented local storage fallback
- ✅ Enhanced folder creation with proper logging
- ✅ Graceful handling of unavailable OneDrive
- ✅ Automatic file saving to `./uploads/` directory

### Previous Fixes
- Fixed Python 3.14 `pkgutil.get_loader()` compatibility
- Resolved port 5000 conflict (using 5001)
- Implemented Device Code Flow for Work accounts
- Converted all UI text from Arabic to English
- Fixed absolute path token file loading

---

## Accessing Stored Files

Files are automatically saved in: `./uploads/V{volunteer_id}/`

Example after running a session as Volunteer 7:
```bash
ls -la ./uploads/V7/

# Output:
# GSR_Data_2026-02-09_161500.csv
# GSR_Recording_2026-02-09_161500.webm
```

---

## Troubleshooting

### Ports in Use
If ports 5001 or 8000 are already in use:
```bash
./STOP.sh  # Force kill processes
./START.sh # Restart
```

### Check Flask Logs
```bash
cat .pids/flask.log
```

### Manual API Test
```bash
# Test authentication
curl http://localhost:5001/api/status

# Test upload
curl -X POST http://localhost:5001/api/upload \
  -H "Content-Type: application/json" \
  -d '{"volunteer_id":"7","filename":"test.csv","file_data":"dGVzdA==","file_type":"csv"}'
```

---

## Notes for Administrator

### OneDrive Provisioning
If you need files to sync to OneDrive in the future:

1. Contact your Microsoft 365 organization admin
2. Request OneDrive provisioning for kfupm@almutlaqunited.com
3. Once enabled, the system will automatically use OneDrive instead of local storage

### Current Solution
Local storage is fully functional and suitable for:
- Development and testing
- Local data collection
- Transfer to network storage via other means

---

## System Status

**Last Updated**: February 9, 2026

✅ **Fully Operational**
- Backend API: Running
- Frontend UI: Running
- Authentication: Working
- File Upload: Working (local storage)
- Data Capture: Working
- Video Recording: Ready

---

## Support

For issues:
1. Check logs: `cat .pids/flask.log`
2. Verify servers: `curl http://localhost:5001/api/status`
3. Check ports: `lsof -ti:5001` and `lsof -ti:8000`
