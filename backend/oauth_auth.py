"""
Interactive OAuth2 Authentication for OneDrive
Opens browser for user login and handles the OAuth callback
"""

import msal
import json
import os
import webbrowser
from datetime import datetime
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

# Configuration
CLIENT_ID = "04b07795-8ddb-461a-bbee-02f9e1bf7b46"
TENANT = "common"  # Use "common" for work/school accounts
REDIRECT_URI = "http://localhost:8765/auth/callback"
SCOPES = ["https://graph.microsoft.com/.default"]
TOKEN_CACHE_FILE = "onedrive_tokens.json"

# Global variables for OAuth flow
auth_code = None
auth_error = None
server_ready = False

class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """Handles OAuth callback from Microsoft"""
    
    def do_get(self):
        global auth_code, auth_error
        
        # Parse query parameters
        from urllib.parse import urlparse, parse_qs
        query = parse_qs(urlparse(self.path).query)
        
        if 'code' in query:
            auth_code = query['code'][0]
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            html = """
            <html>
            <head><title>Authentication Successful</title></head>
            <body style="font-family: Arial; text-align: center; padding: 50px;">
                <h1>✅ Authentication Successful!</h1>
                <p>You can close this window and return to the terminal.</p>
                <p>Your OneDrive access has been granted.</p>
            </body>
            </html>
            """
            self.wfile.write(html.encode())
        else:
            auth_error = query.get('error', ['Unknown error'])[0]
            self.send_response(400)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            html = f"""
            <html>
            <head><title>Authentication Failed</title></head>
            <body style="font-family: Arial; text-align: center; padding: 50px;">
                <h1>❌ Authentication Failed</h1>
                <p>Error: {auth_error}</p>
                <p>Please try again.</p>
            </body>
            </html>
            """
            self.wfile.write(html.encode())
    
    def log_message(self, format, *args):
        # Suppress server logs
        pass

def get_oauth_token():
    """Get OAuth token using interactive browser login"""
    global auth_code, auth_error, server_ready
    
    print("\n" + "="*70)
    print("  🔐 OneDrive OAuth2 Authentication")
    print("="*70)
    print("\nA browser window will open for you to sign in.")
    print("Please use: kfupm@almutlaqunited.com\n")
    
    try:
        # Start HTTP server for callback
        server = HTTPServer(('localhost', 8765), OAuthCallbackHandler)
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()
        server_ready = True
        
        # Create MSAL app
        app = msal.PublicClientApplication(
            CLIENT_ID,
            authority=f"https://login.microsoftonline.com/{TENANT}"
        )
        
        # Get authorization URL
        auth_url = app.get_authorization_request_url(
            scopes=SCOPES,
            redirect_uri=REDIRECT_URI
        )
        
        print("Opening browser for authentication...")
        print(f"Authorization URL: {auth_url}\n")
        
        # Open browser
        webbrowser.open(auth_url)
        
        # Wait for callback
        print("Waiting for authentication... (Ctrl+C to cancel)")
        import time
        max_wait = 300  # 5 minutes
        waited = 0
        while auth_code is None and auth_error is None and waited < max_wait:
            time.sleep(1)
            waited += 1
        
        server.shutdown()
        
        if auth_error:
            print(f"\n❌ Authentication error: {auth_error}")
            return None
        
        if auth_code is None:
            print("\n❌ Authentication timeout")
            return None
        
        # Exchange code for token
        print("\nExchanging authorization code for tokens...")
        
        result = app.acquire_token_by_authorization_code(
            auth_code,
            scopes=SCOPES,
            redirect_uri=REDIRECT_URI
        )
        
        if "access_token" in result:
            print("✅ Successfully obtained access token!")
            return result
        else:
            print(f"❌ Failed to get token: {result.get('error_description')}")
            return None
            
    except Exception as e:
        print(f"❌ Error during authentication: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def save_tokens(tokens):
    """Save tokens to file"""
    try:
        tokens["timestamp"] = datetime.now().isoformat()
        
        # Ensure we're in the backend directory
        token_path = TOKEN_CACHE_FILE
        if not os.path.exists(token_path):
            # Try to find it in current directory or parent
            if os.path.exists(f"backend/{TOKEN_CACHE_FILE}"):
                token_path = f"backend/{TOKEN_CACHE_FILE}"
        
        with open(token_path, "w", encoding="utf-8") as f:
            json.dump(tokens, f, indent=2)
        
        print(f"\n✅ Tokens saved to: {token_path}")
        print(f"   Access Token: {tokens['access_token'][:30]}...") 
        print(f"   Token Type: {tokens.get('token_type', 'Bearer')}")
        
        return True
    except Exception as e:
        print(f"❌ Error saving tokens: {e}")
        return False

def main():
    """Main authentication flow"""
    try:
        tokens = get_oauth_token()
        
        if tokens and save_tokens(tokens):
            print("\n" + "="*70)
            print("✅  SUCCESS! Authentication Complete")
            print("="*70)
            print("\nYour OneDrive account is now connected!")
            print("Files will automatically upload to:")
            print("  📁 /KFUPM_GSR_Project/V{volunteer_id}/")
            print("\nNext: Run './START.sh' to begin recording")
            print("="*70 + "\n")
            return 0
        else:
            print("\n❌ Authentication failed. Please try again.\n")
            return 1
            
    except KeyboardInterrupt:
        print("\n\n❌ Authentication cancelled by user.")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}\n")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
