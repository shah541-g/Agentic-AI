<!-- Task T4: Implement a scheduler script to automate the daily fetching and storing of new newsletters into the database. -->

```python
import time
import sqlite3
from datetime import datetime
from contextlib import contextmanager

# Database file path
DB_FILE = "emails.db"

def init_database():
    """
    Initializes the database schema for storing email details.
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
        date TEXT NOT NULL,
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
    """Context manager for database connections."""
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
    """Inserts a new email record along with associated tags."""
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
            cursor.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)", (tag_name,))
            cursor.execute("SELECT id FROM tags WHERE name = ?", (tag_name,))
            tag_id = cursor.fetchone()["id"]

            cursor.execute(
                "INSERT OR IGNORE INTO email_tags (email_id, tag_id) VALUES (?, ?)",
                (email_id, tag_id)
            )
            
    return email_id

def generate_tags_from_content(body: str, sender: str) -> list:
    """Automatically generates tags based on keywords found in the email body or sender."""
    tags = set()
    content = body.lower()
    
    if any(word in content for word in ["urgent", "asap", "immediate", "critical"]):
        tags.add("urgent")
    if any(word in content for word in ["project", "update", "meeting", "deadline", "report"]):
        tags.add("work")
    if any(word in content for word in ["invoice", "payment", "bill", "subscription", "receipt"]):
        tags.add("finance")
    if any(word in content for word in ["offer", "discount", "sale", "promotion", "deal", "newsletter"]):
        tags.add("newsletter")
        
    if not tags:
        tags.add("general")
        
    return list(tags)

def parse_and_store_email(sender: str, body: str, date: datetime = None, status: str = "unread"):
    """Parses email contents, auto-generates tags, and saves to the SQLite database."""
    tags = generate_tags_from_content(body, sender)
    email_id = insert_email(sender=sender, body=body, status=status, tags=tags, date=date)
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Fetched & Stored | ID: {email_id} | Sender: {sender} | Tags: {tags}")
    return email_id

# =========================================
# Scheduler Implementation (No External Dependencies)
# =========================================

def fetch_new_newsletters():
    """
    Simulates fetching new daily newsletters from an external server/IMAP.
    """
    print("\n--- Running Daily Newsletter Fetcher Job ---")
    
    # Mocking incoming daily newsletters
    mock_daily_newsletters = [
        {
            "sender": "editor@dailydigest.com",
            "body": "Your daily newsletter: Top 10 tech trends, AI updates, and special promotions inside.",
            "date": datetime.now()
        },
        {
            "sender": "finance-weekly@money.com",
            "body": "Weekly invoice review, market insights, and subscription updates for your portfolio.",
            "date": datetime.now()
        }
    ]

    for mail in mock_daily_newsletters:
        parse_and_store_email(
            sender=mail["sender"],
            body=mail["body"],
            date=mail["date"]
        )
    print("--- Job Complete ---\n")

def run_scheduler_loop(interval_seconds: int = 5, run_once_for_demo: bool = True):
    """
    A lightweight, pure-Python scheduler loop that runs tasks periodically 
    without needing third-party libraries like 'schedule' or 'apscheduler'.
    """
    print(f"Scheduler started. Daily newsletter task will trigger every {interval_seconds} seconds.")
    print("(Press Ctrl+C to stop)")
    
    # Run immediately on startup for demonstration purposes
    fetch_new_newsletters()
    
    if run_once_for_demo:
        print("Demo run completed successfully.")
        return

    while True:
        time.sleep(interval_seconds)
        try:
            fetch_new_newsletters()
        except Exception as e:
            print(f"Error executing scheduled job: {e}")

if __name__ == "__main__":
    # Initialize the database schema
    init_database()
    
    # Run the scheduler
    run_scheduler_loop(interval_seconds=10, run_once_for_demo=True)
```

### Usage Note
- **Zero External Dependencies**: Avoids missing package errors (like `ModuleNotFoundError: No module named 'schedule'`) by utilizing a custom, lightweight Python loop combined with `time.sleep()`.
- **Fully Runnable & Automated**: Automatically initializes the SQLite database schema, simulates daily newsletter ingestion, runs auto-tagging logic, and stores records securely. 
- **Extensible**: Adjust the `interval_seconds` parameter or replace the mock fetch block with a real IMAP/API client call for production automation.
