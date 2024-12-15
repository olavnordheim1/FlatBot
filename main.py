from database import ExposeDB, Expose
from email_fetcher import EmailFetcher
from process_exposes import process_all_exposes

def main():
    print("Initializing the database...")
    db_instance = ExposeDB()
    print("Database initialized successfully!")
    print("Fetching emails...")
    email_processor = EmailFetcher(db=db_instance)
    email_processor.fetch_emails()
    print("Email fetching completed!")
    print("Starting processor...")
    process_all_exposes()
    print("All new exposes processed.")

if __name__ == "__main__":
    main()
