from database import init_db
from email_fetcher import fetch_emails
from process_expose import process_all_exposes

def main():
    print("Initializing the database...")
    init_db()
    print("Database initialized successfully!")
    print("Fetching emails...")
    fetch_emails()
    print("Email fetching completed!")
    print("Starting processor...")
    process_all_exposes()
    print("All new exposes processed.")

if __name__ == "__main__":
    main()
