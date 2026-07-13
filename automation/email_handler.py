import os, sys, base64, re

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import GMAIL_CREDENTIALS_PATH, GMAIL_TOKEN_PATH
 
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]
EMAIL_FETCH_LIMIT = 7 #Number of emails it can fetch per request

def _get_gmail_service():
    creds = None

    if os.path.exists(GMAIL_TOKEN_PATH): #try to load an existing token
        try: #If it exists, load the tokens in in
            creds =  Credentials.from_authorized_user_file(GMAIL_TOKEN_PATH, SCOPES)
        except Exception:
            print("[Email]: Token file is corrupt or empty — deleting and re-authenticating...")
            os.remove(GMAIL_TOKEN_PATH)
            creds = None

    if not creds or not creds.valid: #If no valid tokens...
        if creds and creds.expired and creds.refresh_token:
            #Handler to handle expired tokens.json files
            try: 
                creds.refresh(Request())
            except RefreshError: 
                print("[Email]: Token expired or revoked by Google. Deleting stale token and re-authenticating...")
                os.remove(GMAIL_TOKEN_PATH)
                
                #Reauthentication route here instead if ever it finds that the tokens are not available
                if not os.path.exists(GMAIL_CREDENTIALS_PATH):
                    raise FileNotFoundError(
                        f"Gmail credentials not found at '{GMAIL_CREDENTIALS_PATH}'. "
                        "Please download credentials.json from Google Cloud Console."
                    )
                flow = InstalledAppFlow.from_client_secrets_file(GMAIL_CREDENTIALS_PATH, SCOPES)
                creds = flow.run_local_server(port=8081)
                with open(GMAIL_TOKEN_PATH, "w") as token_file:
                    token_file.write(creds.to_json())
        else:
            # First-time setup — opens browser for Google login
            if not os.path.exists(GMAIL_CREDENTIALS_PATH):
                raise FileNotFoundError(
                    f"Gmail credentials not found at '{GMAIL_CREDENTIALS_PATH}'. "
                    "Please download credentials.json from Google Cloud Console."
                )
            flow = InstalledAppFlow.from_client_secrets_file(GMAIL_CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=8081)  # Port 8081 (Dedicated port for the Email)
 
            # Save the token for next time
            with open(GMAIL_TOKEN_PATH, "w") as token_file:
                token_file.write(creds.to_json())
 
    return build("gmail", "v1", credentials=creds)

def get_unread_emails() -> str:
    try:
        service = _get_gmail_service()
 
        # Query for unread emails in the inbox only (not spam, trash, etc.)
        # Gmail uses the same search syntax as the Gmail web UI
        results = service.users().messages().list(
            userId="me",
            q="is:unread in:inbox",
            maxResults=EMAIL_FETCH_LIMIT
        ).execute()
 
        messages = results.get("messages", [])
 
        if not messages:
            spoken = "You have no unread emails, Master."
            print(f"[Email]: {spoken}")
            return spoken
 
        summaries = []
        for msg in messages:
            summary = _extract_email_summary(service, msg["id"])
            if summary:
                summaries.append(summary)
 
        if not summaries:
            return "I found some unread emails but couldn't read their contents, Master."
 
        count = len(summaries)
        intro = f"You have {count} unread email{'s' if count > 1 else ''}, Master. "
 
        # Voice-friendly: "From X, subject Y. From A, subject B."
        body = " ... ".join(summaries)
        spoken = intro + body
 
        print(f"[Email]: {spoken}")
        return spoken
 
    except FileNotFoundError as e:
        print(f"[Email Error]: {e}")
        return "I couldn't find your Gmail credentials. Please set them up first, Master."
        
    except Exception as e:
        print(f"[Email Error]: {e}")
        return "I ran into a problem accessing your Gmail, Master."
        #Fix needed: automatically try to restore tokens.json (for gmail at least) when finding out it expired
    
def _extract_email_summary(service, message_id: str) -> str:
    try:
        msg = service.users().messages().get(
            userId="me",
            id=message_id,
            format="metadata",          # 'metadata' = headers only, no body. Much faster.
            metadataHeaders=["From", "Subject"]
        ).execute()
 
        headers = msg.get("payload", {}).get("headers", [])
 
        # Convert headers list into a lookup dict
        header_map = {h["name"]: h["value"] for h in headers}
 
        sender_raw = header_map.get("From", "Unknown Sender")
        subject = header_map.get("Subject", "No Subject")
        
        sender = _clean_sender(sender_raw)
 
        return f"From {sender}, subject: {subject}"
 
    except Exception as e:
        print(f"[Email Parse Error]: {e}")
        return ""
    
def _clean_sender(raw: str) -> str:
    match = re.match(r'^"?([^"<]+)"?\s*<', raw)
    if match:
        return match.group(1).strip()
    return raw.strip()

def mark_all_fetched_as_read() -> str:
    try:
        service = _get_gmail_service()
 
        results = service.users().messages().list(
            userId="me",
            q="is:unread in:inbox",
            maxResults=EMAIL_FETCH_LIMIT
        ).execute()
 
        messages = results.get("messages", [])
 
        if not messages:
            return "There's nothing unread to mark, Master."
 
        # Batch: remove the UNREAD label from all fetched messages
        for msg in messages:
            service.users().messages().modify(
                userId="me",
                id=msg["id"],
                body={"removeLabelIds": ["UNREAD"]}
            ).execute()
 
        count = len(messages)
        spoken = f"Done. Marked {count} email{'s' if count > 1 else ''} as read, Master."
        print(f"[Email]: {spoken}")
        return spoken
 
    except Exception as e:
        print(f"[Email Error - Mark as read]: {e}")
        return "I couldn't mark those emails as read. Something went wrong."