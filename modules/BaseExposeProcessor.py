import os
import time
import base64
from modules.Database import ExposeDB, Expose
from dotenv import load_dotenv
from modules.StealthBrowser import StealthBrowser
from datetime import datetime

# Base class for real estate automation
class BaseExposeProcessor:
    def __init__(self, email, password, db_file, StealthBrowser):
        self.email = email
        self.password = password
        self.db_file = db_file
        self.StealthBrowser = StealthBrowser

    def login(self, driver):
        raise NotImplementedError

    def scrape_expose(self, StealthBrowser, Expose):
        # Create and return an Expose object
        return Expose

    def apply_for_offer(self, StealthBrowser, Expose):
        raise NotImplementedError

    def handle_page(self, StealthBrowser, Expose):
        raise NotImplementedError

    def process_expose(self, StealthBrowser, Expose):
        expose_id = Expose.expose_id
        offer_link = self.generate_offer_link(Expose)
        print(f"Processing expose: {offer_link}")
        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            print(f"Attempt {attempt}...")
            StealthBrowser.get(offer_link)
            StealthBrowser.load_cookies(self.db_file)
            StealthBrowser.random_wait()
            if StealthBrowser.title != "":
                if self.handle_page(StealthBrowser, expose_id):
                    print(f"Attempt {attempt} succeeded!")
                    return True
                else:
                    print(f"Attempt {attempt} failed.")
            if attempt < max_attempts:
                print("Retrying...\n")
                StealthBrowser.random_wait()
            else:
                print(f"All attempts failed for expose ID {expose_id}.")
                ExposeDB.increase_failures_count(expose_id)
                return False
