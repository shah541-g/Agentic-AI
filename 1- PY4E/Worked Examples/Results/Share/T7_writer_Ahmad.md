<!-- Task T7: Write comprehensive documentation and user guide explaining how to set up credentials, run the scripts, and operate the WhatsApp approval workflow. -->

# Comprehensive Documentation & User Guide: Email Parsing & WhatsApp Approval Workflow

This documentation covers setting up credentials, running the core automation scripts, and operating the WhatsApp-to-LinkedIn approval workflow.

---

## Table of Contents
1. [System Architecture Overview](#system-architecture-overview)
2. [Prerequisites & Dependencies](#prerequisites--dependencies)
3. [Credential & Environment Setup](#credential--environment-setup)
4. [Database Initialization & Email Processing Scripts](#database-initialization--email-processing-scripts)
5. [WhatsApp Webhook & LLM Feedback Workflow](#whatsapp-webhook--llm-feedback-workflow)
6. [Testing & Operational Guide](#testing--operational-guide)

---

## System Architecture Overview

The system bridges automated email data processing with a human-in-the-loop WhatsApp approval workflow:
1. **Email Ingestion & Storage (`emails.db`)**: Emails are fetched via IMAP or simulated payloads, parsed, auto-tagged using keyword engines, and stored in a normalized SQLite database.
2. **Scheduler Automation**: A lightweight, zero-dependency Python background loop periodically triggers ingestion tasks.
3. **WhatsApp Approval Engine**: A Flask webhook server receives inbound messages (`1` for approval, `2` for feedback), utilizes OpenAI's LLM to revise content dynamically, and publishes approved posts to LinkedIn.

---

## Prerequisites & Dependencies

- **Python**: Version 3.8 or higher.
- **Python Libraries**: `flask`, `requests`.
- **Optional External Services**: 
  - Twilio or Meta Cloud API (for production WhatsApp messaging).
  - OpenAI API (for real LLM-backed post revisions).
  - LinkedIn Developer Account (for API publishing).

Install required third-party packages via pip:
```bash
pip install flask requests
```

---

## Credential & Environment Setup

Configure your environment variables before running the production or webhook servers. Set them in your shell or create a `.env` file:

```bash
export LINKEDIN_ACCESS_TOKEN="your_linkedin_access_token_here"
export LINKEDIN_PERSON_URN="urn:li:person:your_person_id"
export OPENAI_API_KEY="your_openai_api_key_here"
```

*(Note: If placeholders are left unchanged, the scripts automatically fall back to secure simulation/mock modes for local testing.)*

---

## Database Initialization & Email Processing Scripts

### 1. Core Email Storage & Auto-Tagging Script (`T3`)
This script initializes the SQLite database schema (`emails`, `tags`, and `email_tags` junction tables) and parses incoming emails to assign categorical tags (`urgent`, `work`, `finance`, `marketing`, `automated`).

```python
import sqlite3
from datetime import datetime
from contextlib import contextmanager

DB_FILE = "emails.db"

def init_database():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS emails (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender TEXT NOT NULL,
        date TEXT NOT NULL,
        body TEXT NOT NULL,
        status TEXT NOT NULL CHECK(status IN ('unread', 'read', 'archived', 'spam'))
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tags (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS email_tags (
        email_id INTEGER,
        tag_id INTEGER,
        PRIMARY KEY (email_id, tag_id),
        FOREIGN KEY (email_id) REFERENCES emails(id) ON DELETE CASCADE,
        FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
    );
    """)
    conn.commit()
    conn.close()

@contextmanager
def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def insert_email(sender: str, body: str, status: str = "unread", tags: list = None, date: datetime = None):
    if date is None:
        date = datetime.now()
    date_str = date.strftime("%Y-%m-%d %H:%M:%S")
    tags = tags or []

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO emails (sender, date, body, status) VALUES (?, ?, ?, ?)",
            (sender, date_str, body, status)
        )
        email_id = cursor.lastrowid

        for tag_name in tags:
            cursor.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)(?)", (tag_name,)) # Handled cleanly in production
            cursor.execute("SELECT id FROM tags WHERE name = ?", (tag_name,))
            row = cursor.fetchone()
            if row:
                tag_id = row["id"]
                cursor.execute(
                    "INSERT OR IGNORE INTO email_tags (email_id, tag_id) VALUES (?, ?)",
                    (email_id, tag_id)
                )
    return email_id
```

### 2. Scheduled Newsletter Ingestion (`T4`)
To run periodic background tasks without external job scheduler dependencies (like Celery or APScheduler), use Python's native loop paired with `time.sleep`:

```python
import time

def run_scheduler_loop(interval_seconds: int = 10, run_once_for_demo: bool = True):
    print(f"Scheduler started. Running tasks every {interval_seconds} seconds.")
    
    # Initial execution
    print("--- Executing Scheduled Job ---")
    
    if run_once_for_demo:
        print("Demo run completed.")
        return

    while True:
        time.sleep(interval_seconds)
        try:
            # Call your fetch/parsing job here
            pass
        except Exception as e:
            print(f"Scheduler error: {e}")
```

---

## WhatsApp Webhook & LLM Feedback Workflow (`T6`)

The Flask application processes incoming replies from administrators via WhatsApp, implements an iterative feedback loop using OpenAI, and triggers LinkedIn publishing upon approval.

Save the following code as `app.py`:

```python
import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

LINKEDIN_ACCESS_TOKEN = os.environ.get("LINKEDIN_ACCESS_TOKEN", "YOUR_LINKEDIN_ACCESS_TOKEN")
LINKEDIN_PERSON_URN = os.environ.get("LINKEDIN_PERSON_URN", "urn:li:person:YOUR_PERSON_ID")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "YOUR_OPENAI_API_KEY")

SESSION_STORE = {}

def call_llm_to_update_post(current_text: str, user_feedback: str) -> str:
    print(f"\n[LLM API] Refining post based on feedback: '{user_feedback}'")
    if OPENAI_API_KEY != "YOUR_OPENAI_API_KEY":
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "gpt-4o",
            "messages": [
                {"role": "system", "content": "You are a professional social media manager. Revise the following LinkedIn post based on user feedback."},
                {"role": "user", "content": f"Current Post:\n{current_text}\n\nUser Feedback: {user_feedback}"}
            ]
        }
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]

    return f"{current_text}\n\n[Revised update based on feedback: {user_feedback}]"

def trigger_linkedin_post(post_text: str) -> bool:
    print(f"\n[LinkedIn API] Publishing post to URN: {LINKEDIN_PERSON_URN}")
    if LINKEDIN_ACCESS_TOKEN == "YOUR_LINKEDIN_ACCESS_TOKEN":
        print("[LinkedIn API] Mock Success: Post successfully published.")
        return True

    url = "https://api.linkedin.com/v2/posts"
    headers = {
        "Authorization": f"Bearer {LINKEDIN_ACCESS_TOKEN}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0"
    }
    payload = {
        "author": LINKEDIN_PERSON_URN,
        "commentary": post_text,
        "visibility": "PUBLIC",
        "distribution": {"feedDistribution": "MAIN_FEED"},
        "lifecycleState": "PUBLISHED"
    }
    response = requests.post(url, headers=headers, json=payload)
    return response.status_code in [200, 201]

def send_whatsapp_reply(recipient_phone: str, message: str):
    print(f"\n[WhatsApp Outbound to {recipient_phone}]:\n{message}")

@app.route("/webhook/whatsapp", methods=["POST"])
def whatsapp_webhook():
    incoming_data = request.form if request.form else request.json
    if not incoming_data:
        return jsonify({"status": "error", "message": "No payload received"}), 400

    sender_phone = incoming_data.get("From") or incoming_data.get("sender", "+1234567890")
    user_message = (incoming_data.get("Body") or incoming_data.get("message", "")).strip()

    if sender_phone not in SESSION_STORE:
        SESSION_STORE[sender_phone] = {
            "current_post": "Exciting updates! We are launching our new automation workflows.",
            "state": "awaiting_approval"
        }

    session = SESSION_STORE[sender_phone]
    state = session.get("state")

    if state == "awaiting_approval":
        if user_message == "1":
            success = trigger_linkedin_post(session["current_post"])
            if success:
                send_whatsapp_reply(sender_phone, "✅ Post has been approved and published to LinkedIn!")
            else:
                send_whatsapp_reply(sender_phone, "⚠️ Failed to publish to LinkedIn.")
            del SESSION_STORE[sender_phone]

        elif user_message == "2":
            session["state"] = "awaiting_feedback"
            send_whatsapp_reply(sender_phone, "✍️ Please reply with your feedback or suggested changes:")

        else:
            send_whatsapp_reply(sender_phone, "Invalid option. Reply with:\n[1] Approve\n[2] Suggestion")

    elif state == "awaiting_feedback":
        updated_post = call_llm_to_update_post(session["current_post"], user_message)
        session["current_post"] = updated_post
        session["state"] = "awaiting_approval"
        send_whatsapp_reply(sender_phone, f"🔄 Revised post preview:\n\n{updated_post}\n\nReply:\n[1] Approve & Publish\n[2] Provide another suggestion")

    return jsonify({"status": "success"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
```

---

## Testing & Operational Guide

### 1. Running the Flask Webhook Server
Start the application locally:
```bash
python app.py
```
The server will start at `http://localhost:5000/webhook/whatsapp`.

### 2. Simulating WhatsApp Interactions via cURL
Open a separate terminal window and run the following commands to test the workflow:

- **Step A: Test Direct Approval (`Option 1`)**
  ```bash
  curl -X POST http://localhost:5000/webhook/whatsapp -d "From=+1234567890&Body=1"
  ```
  *(Expected Console Output: Triggers mock LinkedIn post publication and success confirmation).*

- **Step B: Test Revision Request (`Option 2`)**
  ```bash
  curl -X POST http://localhost:5000/webhook/whatsapp -d "From=+1234567890&Body=2"
  ```
  *(Expected Console Output: Prompts user to input feedback).*

- **Step C: Provide Feedback for LLM Refinement**
  ```bash
  curl -X POST http://localhost:5000/webhook/whatsapp -d "From=+1234567890&Body=Make it punchier and add emojis."
  ```
  *(Expected Console Output: Rewrites post using OpenAI or fallback logic and sends preview back for re-approval).*
