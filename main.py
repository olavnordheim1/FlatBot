import os
import importlib
from modules.Database import ExposeDB, Expose
from modules.EmailFetcher import EmailFetcher
from modules.StealthBrowser import StealthBrowser

def process_all_exposes(db):
    exposes = db.get_unprocessed_exposes()
    if not exposes:
        print("No unprocessed exposes found.")
        return
    stealth_chrome = StealthBrowser()

    for expose_row in exposes:
        expose = Expose(**expose_row)
        source_key = expose.source
        print(f"Debug: Processing source key: {source_key}")
        try:
            processor_module = importlib.import_module(f"{source_key}_processor")
            processor_module.process_expose(stealth_chrome, expose)
        except ModuleNotFoundError:
            print(f"Processor module for {source_key} not found")
        except AttributeError:
            print(f"process_expose function missing in module {source_key}_processor")
        except Exception as e:
            print(f"Error processing expose from {source_key}: {e}")

    stealth_chrome.kill()

def main():
    print("Initializing the database...")
    db_instance = ExposeDB()
    print("Database initialized successfully!")
    print("Fetching emails...")
    email_processor = EmailFetcher(db=db_instance)
    email_processor.fetch_emails()
    print("Email fetching completed!")
    print("Starting processor...")
    process_all_exposes(db_instance)
    print("All new exposes processed.")

if __name__ == "__main__":
    main()