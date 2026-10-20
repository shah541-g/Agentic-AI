import json
import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

import base64
import time

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from googleapiclient.errors import HttpError
from html.parser import HTMLParser

CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "tokens.json"

SCOPES = [
  "https://www.googleapis.com/auth/gmail.readonly"
]

def get_gmail_service():
  credentials = None
  
  # Step 1: Load Previously Saved OAuth Tokens
  if os.path.exists(TOKEN_FILE):
    credentials = Credentials.from_authorized_user_file(
      TOKEN_FILE,
      SCOPES
    )
  
  # Step 2. Refresh Expired Credentials or Authorize if necessary
  if not credentials or not credentials.valid:
    
    if credentials and credentials.refresh_token:
      credentials.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(
        CREDENTIALS_FILE,
        SCOPES
      )  
      credentials = flow.run_local_server(port=0)
      
    # Step 3. Save updated tokens for the next run.
    with open(TOKEN_FILE, "w", encoding="utf-8") as file:
      file.write(credentials.to_json())
  
  service = build(
    "gmail",
    "v1",
    credentials=credentials
  )
  
  return service


def extract_body(payload):
  plain_parts = []
  html_parts = []
  
  def walk(part):
    mime_type = part.get("mimeType","")
    body_data = part.get("body",{}).get("data")
    
    if body_data:
      decoded = base64.urlsafe_b64decode(
        body_data + "=" * (-len(body_data)%4)
      ).decode("utf-8", errors="replace")

      if mime_type == 'text/plain':
        plain_parts.append(decoded)
      
      elif mime_type == 'text/html':
        html_parts.append(decoded)
    
    for child in part.get("parts", []):
      walk(child)
    
  walk(payload)
  
  if plain_parts:
    return "\n".join(plain_parts)
  if html_parts:
    class TextExtractor(HTMLParser):
      def __init__(self):
        super().__init__()
        self.text = []
        
      def handle_data(self, data):
        self.text.append(data)
    
    parser = TextExtractor()
    
    for html in html_parts:
      parser.feed(html)
    
    return "\n".join(parser.text)
  
  return ""


def fetch_unread_emails(service):
    emails = []
    page_token = None

    while True:
        try:
            response = service.users().messages().list(
                userId="me",
                q="is:unread newer_than:1d",
                maxResults=100,
                pageToken=page_token
            ).execute(num_retries=3)

        except HttpError as error:
            print(f"Could not list unread messages: {error}")
            break

        messages = response.get("messages", [])

        for message_ref in messages:
            message_id = message_ref["id"]

            try:
                message = service.users().messages().get(
                    userId="me",
                    id=message_id,
                    format="full"
                ).execute(num_retries=3)

                headers = message.get("payload", {}).get("headers", [])

                header_map = {
                    header["name"].lower(): header["value"]
                    for header in headers
                }

                email_record = {
                    "id": message_id,
                    "thread_id": message.get("threadId"),
                    "sender": header_map.get("from", ""),
                    "to": header_map.get("to", ""),
                    "subject": header_map.get("subject", ""),
                    "date": header_map.get("date", ""),
                    "body": extract_body(message["payload"]),
                    "labels": message.get("labelIds", [])
                }

                emails.append(email_record)

                print(
                    f"Fetched unread email: "
                    f"{email_record['subject']}"
                )

            except HttpError as error:
                print(f"Skipping email {message_id}: {error}")

            time.sleep(0.05)

        page_token = response.get("nextPageToken")

        if not page_token:
            break

    return emails

def save_emails(emails):
  os.makedirs("data", exist_ok=True)

  result = {
      "fetched_at": datetime.now(timezone.utc).isoformat(),
      "total_emails": len(emails),
      "emails": emails
  }

  output_file = os.path.join("output", "emails.json")

  with open(output_file, "w", encoding="utf-8") as file:
      json.dump(
          result,
          file,
          indent=2,
          ensure_ascii=False
      )

  print(f"\nTotal emails fetched: {len(emails)}")
  print(f"Saved to: {output_file}")  

def main():
    try:
        print("Connecting to Gmail...")

        service = get_gmail_service()

        print("Connected successfully.")
        print("Fetching emails...")

        emails = fetch_unread_emails(service)

        save_emails(emails)

    except Exception as error:
        print(f"Program failed: {error}")


if __name__ == "__main__":
    main()
      

      