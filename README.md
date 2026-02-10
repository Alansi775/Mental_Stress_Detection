# GSR Stress Monitor with OneDrive Upload

A complete system for recording and analyzing Galvanic Skin Response (GSR) data with automatic upload to OneDrive using secure Device Code Flow authentication.

## Quick Start (30 seconds)

```bash
# 1. First time only - install everything
./setup.sh

# 2. Start all services
./START.sh

# 3. Open browser to:
http://localhost:8000/index.html

# 4. When done - stop everything
./STOP.sh
```

That's it! Everything runs automatically.

---

## What This Does

1. **GSR Monitoring**: Reads data from ESP32 microcontroller
2. **Video Recording**: Captures video with live data overlay
3. **Data Export**: Saves CSV files with timestamps and readings
4. **OneDrive Sync**: Automatically uploads files to OneDrive
5. **Web UI**: Simple browser-based interface

---

## System Architecture

```
┌─────────────────┐
│  Web UI         │  (port 8000)
│  - Camera       │
│  - Controls     │
│  - Display      │
└────────┬────────┘
         │
         │ HTTP requests
         ▼
┌─────────────────┐
│  Flask Backend  │  (port 5000)
│  - File upload  │
│  - OneDrive API │
│  - Retry logic  │
└────────┬────────┘
         │
         │ HTTPS
         ▼
┌─────────────────┐
│  Microsoft      │
│  Graph API      │
│  OneDrive       │
└─────────────────┘
```

---

## File Structure

```
Mental_Stress_Detection/
├── src/
│   └── main.cpp              # ESP32 firmware
├── ui/
│   └── index.html            # Web interface
├── backend/
│   ├── device_auth.py        # OneDrive authentication
│   ├── onedrive_uploader.py  # Flask server
│   └── requirements.txt       # Python dependencies
├── setup.sh                  # One-time setup script
├── START.sh                  # Start everything
├── STOP.sh                   # Stop everything
└── README.md                 # This file
```

---

## Setup Instructions

### Prerequisites

- macOS with Python 3.7+
- pip3 (comes with Python)
- Internet connection
- OneDrive account

### Installation

Run once:

```bash
chmod +x setup.sh START.sh STOP.sh
./setup.sh
```

This will:
1. Create Python virtual environment (`venv`)
2. Install Flask, MSAL, and other dependencies
3. Show setup complete message

### Authentication (OneDrive)

After first run of `./START.sh`, you may need to authenticate:

1. The system will show a Microsoft login URL
2. Open the URL in your browser
3. Sign in with your OneDrive account
4. Grant permissions when prompted
5. Device tokens are saved automatically

---

## Operation

### Starting Everything

```bash
./START.sh
```

This starts:
- Flask backend on `http://localhost:5000`
- HTTP server on `http://localhost:8000`

Then open: `http://localhost:8000/index.html`

### Using the Application

1. Enter volunteer number
2. Click "Open Camera" to start recording
3. Click "Start Session" to begin monitoring
4. Follow the 5-stage protocol:
   - Calibration (20 sec)
   - Normal (4 min)
   - Stress (3 min)
   - Relax (1 min)
   - Complete
5. Session automatically stops
6. CSV and video files auto-upload to OneDrive

### Stopping Everything

```bash
./STOP.sh
```

Kills Flask and HTTP server cleanly.

---

## OneDrive Storage

Files are automatically organized in OneDrive:

```
OneDrive/
└── KFUPM_GSR_Project/
    ├── V1/
    │   ├── GSR_Data.csv
    │   └── V1.webm
    ├── V2/
    │   ├── GSR_Data.csv
    │   └── V2.webm
    └── V3/
        └── ...
```

---

## APIs

### Upload File
```
POST http://localhost:5000/api/upload

{
  "volunteer_id": "1",
  "filename": "GSR_Data.csv",
  "file_data": "base64_encoded_content",
  "file_type": "csv"
}
```

### Check Status
```
GET http://localhost:5000/api/status
```

---

## Troubleshooting

### Problem: "externally-managed-environment"
**Solution**: Run `./setup.sh` to create virtual environment

### Problem: "Module not found" (Flask, msal, etc.)
**Solution**: 
```bash
./setup.sh
```

### Problem: Port already in use
**Solution**: 
```bash
./STOP.sh    # Stop running services
sleep 2
./START.sh   # Start again
```

### Problem: Files not uploading
Check:
1. Internet connection is active
2. Flask is running: `curl http://localhost:5000/api/status`
3. OneDrive tokens valid (re-run setup if needed)

### Problem: Camera not working
Check:
1. Browser permission granted
2. Camera device connected
3. Try another browser (Firefox, Chrome)

---

## Environment Variables

Created automatically in `venv/`. To customize, edit `backend/onedrive_uploader.py`:

- `FLASK_HOST`: 0.0.0.0
- `FLASK_PORT`: 5000
- `CHUNK_SIZE`: 327680 (320KB for resumable uploads)

---

## Security Notes

- Tokens stored locally in `backend/onedrive_tokens.json`
- No passwords stored - uses OAuth 2.0
- Device Code Flow = no password needed
- Mark `onedrive_tokens.json` as secret

---

## Performance

- CSV upload: < 1 second
- Video upload: 2-5 minutes (depends on file size)
- Automatic retry: 3 attempts if upload fails
- Resumable uploads: Restart safely if interrupted

---

## Dependencies

All installed via `./setup.sh`:

- Flask 2.3.2
- Flask-CORS 4.0.0  
- msal 1.24.0 (Microsoft Auth)
- requests 2.31.0
- python-dotenv 1.0.0

---

## ESP32 Configuration

The ESP32 uses static IP: `10.155.83.100`

To change:
1. Edit `src/main.cpp`, find IP configuration
2. Recompile and upload to ESP32
3. Update UI IP field if needed

Default WiFi SSID: `TEKMER WIFI`

---

## Development

### Running Flask manually:
```bash
source venv/bin/activate
python3 backend/onedrive_uploader.py
```

### Running HTTP server manually:
```bash
cd ui
python3 -m http.server 8000
```

### Checking logs:
```bash
tail -f .pids/flask.log
```

---

## Support

For issues:
1. Check this README
2. Run `./STOP.sh` then `./START.sh` 
3. Check browser console (F12)
4. Verify all network connections

---

## License

MIT License - Free to use and modify

---

## Project Structure Summary

| Component | Location | Purpose |
|-----------|----------|---------|
| Web UI | `ui/index.html` | User interface |
| ESP32 | `src/main.cpp` | Hardware control |
| Backend | `backend/onedrive_uploader.py` | File upload server |
| Auth | `backend/device_auth.py` | OneDrive login |
| Setup | `setup.sh` | One-time installation |
| Start | `START.sh` | Launch everything |
| Stop | `STOP.sh` | Clean shutdown |

---

## Next Steps

1. Run `./setup.sh` once
2. Run `./START.sh` to begin
3. Open `http://localhost:8000/index.html`
4. Start monitoring!

That's all you need to know. The system handles everything else automatically.

---

**Version**: 2.0 (OneDrive Sync Edition)  
**Last Updated**: February 2026
