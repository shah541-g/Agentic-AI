import sqlite3
import imaplib
import email
from email.header import decode_header
from datetime import datetime
from contextlib import contextmanager
import re

# Database file path
DB_FILE = "emails.db"

def init_database():
    """
    Initializes the database schema for storing email details.
    
    Tables created:
    - emails: Stores core email attributes (sender, date, body, status).
    - tags: Stores unique tag names.
    - email_tags: Junction table for many-to-many relationship between emails and tags.
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Enable foreign key support in SQLite
    cursor.execute("PRAGMA foreign_keys = ON;")

    # 1. Emails Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS emails (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender TEXT NOT NULL,
        date TEXT NOT NULL, -- Stored in ISO 8601 format (YYYY-MM-DD HH:MM:SS)
        body TEXT NOT NULL,
        status TEXT NOT NULL CHECK(status IN ('unread', 'read', 'archived', 'spam'))
    );
    """)

    # 2. Tags Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tags (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    );
    """)

    # 3. Email-Tags Junction Table (Many-to-Many)
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
    """
    Context manager for database connections to ensure proper closing and 
    transaction management.
    """
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row  # Enables column access by name: row['sender']
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

# ==========================================
# Data Access Functions (CRUD Operations)
# ==========================================

def insert_email(sender: str, body: str, status: str = "unread", tags: list = None, date: datetime = None):
    """Inserts a new email record along with associated tags."""
    if date is None:
        date = datetime.now()
    
    date_str = date.strftime("%Y-%m-%d %H:%M:%S")
    tags = tags or []

    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Insert email
        cursor.execute(
            "INSERT INTO emails (sender, date, body, status) VALUES (?, ?, ?, ?)",
            (sender, date_str, body, status)
        )
        email_id = cursor.lastrowid

        # Insert and link tags
        for tag_name in tags:
            # Insert tag if it doesn't already exist
            cursor.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)", (tag_name,))
            
            # Retrieve tag id
            cursor.execute("SELECT id FROM tags WHERE name = ?", (tag_name,))
            tag_id = cursor.fetchone()["id"]

            # Link email and tag
            cursor.execute(
                "INSERT OR IGNORE INTO email_tags (email_id, tag_id) VALUES (?, ?)",
                (email_id, tag_id)
            )
            
    return email_id

def fetch_emails_by_tag(tag_name: str):
    """Retrieves all emails associated with a specific tag."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT e.* FROM emails e
            JOIN email_tags et ON e.id = et.email_id
            JOIN tags t ON et.tag_id = t.id
            WHERE t.name = ?
        """, (tag_name,))
        return [dict(row) for row in cursor.fetchall()]

# ==========================================
# Email Processing & Tag Generation
# ==========================================

def generate_tags_from_content(body: str, sender: str) -> list:
    """
    Automatically generates tags based on keywords found in the email body or sender.
    """
    tags = set()
    content = body.lower()
    
    # Keyword-based tag generation logic
    if any(word in content for word in ["urgent", "asap", "immediate", "critical"]):
        tags.add("urgent")
    if any(word in content for word in ["project", "update", "meeting", "deadline", "report"]):
        tags.add("work")
    if any(word in content for word in ["invoice", "payment", "bill", "subscription", "receipt"]):
        tags.add("finance")
    if any(word in content for word in ["offer", "discount", "sale", "promotion", "deal"]):
        tags.add("marketing")
        
    # Sender-based tagging
    if "no-reply" in sender.lower() or "support" in sender.lower():
        tags.add("automated")
        
    # Default fallback tag if none matched
    if not tags:
        tags.add("general")
        
    return list(tags)

def parse_and_store_email(sender: str, body: str, date: datetime = None, status: str = "unread"):
    """
    Parses email contents, auto-generates tags, and saves to the SQLite database.
    """
    # 1. Generate tags automatically from content
    tags = generate_tags_from_content(body, sender)
    
    # 2. Store into the database
    email_id = insert_email(sender=sender, body=body, status=status, tags=tags, date=date)
    print(f"[{email_id}] Parsed & Saved | Sender: {sender} | Tags: {tags}")
    return email_id

# ==========================================
# Execution / Verification
# ==========================================
if __name__ == "__main__":
    # Initialize the database and tables
    init_database()
    print("Database schema initialized successfully using built-in sqlite3.\n")

    # Simulate fetching incoming emails (e.g., from IMAP or API source)
    mock_fetched_emails = [
        {
            "sender": "boss@company.com",
            "body": "URGENT: Please send the project update report before the deadline today.",
            "date": datetime.now()
        },
        {
            "sender": "billing@netflix.com",
            "body": "Your monthly subscription invoice and payment receipt are ready.",
            "date": datetime.now()
        },
        {
            "sender": "promo@shop.com",
            "body": "Big sale! Get 50% discount on all items with this exclusive offer.",
            "date": datetime.now()
        }
    ]

    print("--- Processing and Storing Fetched Emails ---")
    for mail in mock_fetched_emails:
        parse_and_store_email(
            sender=mail["sender"],
            body=mail["body"],
            date=mail["date"]
        )

    print("\n--- Querying Database by Generated Tags ---")
    for search_tag in ["urgent", "finance", "marketing"]:
        tagged_emails = fetch_emails_by_tag(search_tag)
        print(f"\nEmails tagged with '{search_tag}':")
        for email_item in tagged_emails:
            print(f" - From: {email_item['sender']} | Body: {email_item['body'][:50]}...")
