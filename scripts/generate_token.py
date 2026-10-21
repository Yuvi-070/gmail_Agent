"""
L&D Operations Copilot — OAuth Refresh Token Generator

Run this script ONCE locally to generate an OAuth refresh token.
You will need the client_secret.json file from GCP Console.

Usage:
    1. Download OAuth client JSON from GCP Console → Credentials
    2. Save it as 'client_secret.json' in the project root
    3. Run: python scripts/generate_token.py
    4. A browser window will open for Google login
    5. Grant all requested permissions
    6. The refresh token will be printed — save it securely!
"""

import json
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google_auth_oauthlib.flow import InstalledAppFlow

# These must match the scopes in src/auth.py
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/spreadsheets.readonly",
]

CLIENT_SECRET_FILE = "client_secret.json"


def main():
    print("=" * 60)
    print("L&D Operations Copilot — OAuth Token Generator")
    print("=" * 60)
    print()

    # Check for client_secret.json
    if not os.path.exists(CLIENT_SECRET_FILE):
        print(f"❌ Error: '{CLIENT_SECRET_FILE}' not found!")
        print()
        print("Steps to fix:")
        print("1. Go to: https://console.cloud.google.com/apis/credentials")
        print("2. Click on your OAuth 2.0 Client ID")
        print("3. Click 'Download JSON'")
        print(f"4. Save it as '{CLIENT_SECRET_FILE}' in the project root")
        print("5. Run this script again")
        sys.exit(1)

    print(f"✅ Found {CLIENT_SECRET_FILE}")
    print()
    print("Requesting the following OAuth scopes:")
    for scope in SCOPES:
        short_name = scope.split("/")[-1]
        print(f"  • {short_name}")
    print()
    print("A browser window will open. Please log in with:")
    print("  📧 yuvrajtale070@gmail.com")
    print()
    input("Press Enter to continue...")

    # Run the OAuth flow
    flow = InstalledAppFlow.from_client_secrets_file(
        CLIENT_SECRET_FILE,
        scopes=SCOPES,
        redirect_uri="urn:ietf:wg:oauth:2.0:oob",
    )

    # Use run_local_server for desktop flow
    credentials = flow.run_local_server(
        port=8090,
        prompt="consent",
        access_type="offline",
    )

    print()
    print("=" * 60)
    print("✅ SUCCESS! Here are your credentials:")
    print("=" * 60)
    print()
    print(f"🔑 Refresh Token:")
    print(f"   {credentials.refresh_token}")
    print()
    print(f"🔑 Access Token (temporary, will expire):")
    print(f"   {credentials.token[:50]}...")
    print()
    print("=" * 60)
    print("NEXT STEPS:")
    print("=" * 60)
    print()
    print("1. Copy the Refresh Token above")
    print("2. Store it in Google Secret Manager:")
    print('   gcloud secrets create OAUTH_REFRESH_TOKEN --data-file=-')
    print("   (paste the token and press Ctrl+D)")
    print()
    print("3. Or add it to your .env file:")
    print(f"   OAUTH_REFRESH_TOKEN={credentials.refresh_token}")
    print()
    print("⚠️  IMPORTANT: Never commit the refresh token to git!")
    print()


if __name__ == "__main__":
    main()
