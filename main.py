import os
import time
from datetime import datetime
import random
import importlib
import logging
from modules.Database import ExposeDB, Expose
from modules.EmailFetcher import EmailFetcher


logger = logging.getLogger(__name__)
log_level = logging.INFO

def init_log():    # Create logs directory if it doesn't exist
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
    os.makedirs(log_dir, exist_ok=True)
    # Generate log file name
    current_time = datetime.now()
    log_file = f"Flatbot_{current_time.month}_{current_time.year}.log"
    log_file_path = os.path.join(log_dir, log_file)
    logging.basicConfig(filename=log_file_path, level=log_level)


def main():
    init_log()
    # Temporarily add console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    logger.warning(">----------------------- Flatbot starting! -----------------------<")
    logger.debug('Log started')
    print("Initializing the database...")
    db_instance = ExposeDB()
    logger.info("Database initialized successfully!")
    logger.info("Fetching emails...")
    email_processor = EmailFetcher(db_instance)
    email_processor.fetch_emails()
    logger.info("Email fetching completed!")

    logger.info("Starting processor...")
    exposes = db_instance.get_unprocessed_exposes()
    if not exposes:
        logger.info("No unprocessed exposes found.")
        return
    for expose in exposes:
        try:
            processor_module = importlib.import_module(f"modules.{expose.source}_processor")
            processor_class = getattr(processor_module, f"{expose.source}_processor", None)
            if not processor_class:
                logger.error(f"Processor class for {expose.source} not found")
                continue

            processor_instance = processor_class()
            expose, success = processor_instance.process_expose(expose)
            if success:
                db_instance.update_expose(expose)
                
        except ModuleNotFoundError:
            logger.error(f"Processor module for {expose.source} not found")
        except AttributeError as e:
            logger.error(f"Error accessing processor class: {e}")
        except Exception as e:
            logger.error(f"Error processing expose from {expose.source}: {e}")

    logger.info("All new exposes processed.")
    random_wait(300, 900)

def random_wait(min_seconds=2, max_seconds=5):
    wait_time = random.uniform(min_seconds, max_seconds)
    logger.info(f"Waiting for {wait_time:.2f} seconds...")
    time.sleep(wait_time)

############################################################
if __name__ == "__main__":
    main()
