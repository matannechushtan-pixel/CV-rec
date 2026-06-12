"""
Gmail OAuth2 authentication for the job alert agent.

First-time setup:
  python3 core/gmail_auth.py
This opens a browser, you log in, and saves token.json locally.
After that, token.json auto-refreshes — no browser needed again.
"""
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials   import Credentials
from google_auth_oauthlib.flow   import InstalledAppFlow
from googleapiclient.discovery   import build

# Read-only scope — we never send or delete emails
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly",
          "https://www.googleapis.com/auth/gmail.modify"]

_BASE = Path(__file__).parent.parent   # backend/

CREDENTIALS_FILE = _BASE / "gmail_credentials.json"
TOKEN_FILE       = _BASE / "gmail_token.json"


def get_gmail_service():
    """
    Return an authenticated Gmail API service object.
    Uses cached token if available, refreshes automatically.
    """
    creds = None

    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(
            str(TOKEN_FILE), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDENTIALS_FILE.exists():
                raise FileNotFoundError(
                    f"Missing {CREDENTIALS_FILE}\n"
                    "Download it from Google Cloud Console:\n"
                    "APIs & Services → Credentials → OAuth 2.0 Client → Download JSON"
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)

        TOKEN_FILE.write_text(creds.to_json())

    return build("gmail", "v1", credentials=creds)


if __name__ == "__main__":
    print("Authenticating with Gmail...")
    svc = get_gmail_service()
    profile = svc.users().getProfile(userId="me").execute()
    print(f"Connected as: {profile['emailAddress']}")
    print(f"Token saved → {TOKEN_FILE}")
    print("Authentication complete. You can now run the agent.")
