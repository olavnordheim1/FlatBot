import os
import time
import random
import importlib
from modules.Database import ExposeDB, Expose
from modules.EmailFetcher import EmailFetcher
from modules.StealthBrowser import StealthBrowser


def main():
    print("Initializing the database...")
    db_instance = ExposeDB()
    print("Database initialized successfully!")
    print("Fetching emails...")
    email_processor = EmailFetcher(db_instance)
    email_processor.fetch_emails()
    print("Email fetching completed!")

    print("Starting processor...")
    exposes = db_instance.get_unprocessed_exposes()
    if not exposes:
        print("No unprocessed exposes found.")
        return
    for expose in exposes:
        try:
            processor_module = importlib.import_module(f"modules.{expose.source}_processor")
            processor_class = getattr(processor_module, f"{expose.source}_processor", None)
            if not processor_class:
                print(f"Processor class for {expose.source} not found")
                continue

            processor_instance = processor_class()
            expose, success = processor_instance.process_expose(expose)
            if success:
                db_instance.update_expose(expose)
                
        except ModuleNotFoundError:
            print(f"Processor module for {expose.source} not found")
        except AttributeError as e:
            print(f"Error accessing processor class: {e}")
        except Exception as e:
            print(f"Error processing expose from {expose.source}: {e}")

    print("All new exposes processed.")
    random_wait(300, 900)

def random_wait(min_seconds=2, max_seconds=5):
    wait_time = random.uniform(min_seconds, max_seconds)
    print(f"Waiting for {wait_time:.2f} seconds...")
    time.sleep(wait_time)

############################################################
if __name__ == "__main__":
    main()
