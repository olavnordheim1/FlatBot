from database import init_db
from email_fetcher import fetch_emails

def main():
    print("Initializing the database...")
    init_db()
    print("Database initialized successfully!")

    print("Fetching emails...")
    fetch_emails()
    print("Email fetching completed!")

if __name__ == "__main__":
    main()
