import sqlite3
from datetime import datetime
from contextlib import contextmanager

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
# Execution / Verification
# ==========================================
if __name__ == "__main__":
    # Initialize the database and tables
    init_database()
    print("Database schema initialized successfully using built-in sqlite3.")

    # Insert a test email
    email_id = insert_email(
        sender="alice@example.com",
        body="Hello, this is a test email regarding the project update.",
        status="unread",
        tags=["work", "urgent"]
    )
    print(f"Inserted test email with ID: {email_id}")

    # Query emails by tag
    work_emails = fetch_emails_by_tag("work")
    print("Emails tagged with 'work':")
    for email in work_emails:
        print(f" - From: {email['sender']} | Status: {email['status']} | Body: {email['body']}")
