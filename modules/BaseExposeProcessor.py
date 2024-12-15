import os
import time
import base64
from modules.Database import ExposeDB
from modules.Expose import Expose
from dotenv import load_dotenv
from modules.StealthBrowser import StealthBrowser
from datetime import datetime

# Base class for real estate automation
class BaseExposeProcessor:
    def __init__(self, name, domain, email, password, application_text, ExposeDB, StealthBrowser):
        self.name = name
        self.domain = domain
        self.email = email
        self.password = password
        self.application_text = application_text
        self.database = ExposeDB
        self.StealthBrowser = StealthBrowser
        self.debug = False

    def set_debug(self, debug):
        self.debug = debug
        self._debug_log(f"Debug mode set to {self.debug}")

    def _debug_log(self, message):
        if self.debug:
            print(message)

    def get_name(self):
        return self.name
    
    def get_domain(self):
        return self.domain
    
    def set_application_text(self, application_text):
        self.application_text = application_text
    
    def extract_expose_link(self, subject, email_body):
        self._debug_log(self.name)
        raise NotImplementedError

    def generate_expose_link(self, expose):
        self._debug_log(self.name)
        raise NotImplementedError
    
    #must return true if succesful
    def perform_login(self):
        self._debug_log(self.name)
        raise NotImplementedError

    #must return true if succesful    
    def check_login(self):
        self._debug_log(self.name)
        raise NotImplementedError
    
    #must return true if succesful
    def scrape_expose(self, Expose):
        self._debug_log(self.name)
        # Create and return an Expose object
        return Expose

    #must return true if succesful
    def apply_for_offer(self, Expose):
        self._debug_log(self.name)
        raise NotImplementedError

    #must return true if succesful
    def handle_page(self, Expose):
        self._debug_log(self.name)
        raise NotImplementedError

    def process_expose(self, Expose):
        expose_id = Expose.expose_id
        offer_link = self.generate_offer_link(Expose)
        self._debug_log(f"Processing expose: {offer_link}")
        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            self._debug_log(f"Attempt {attempt}...")
            self.StealthBrowser.get(offer_link)
            self.StealthBrowser.load_cookies(self.name)
            self.StealthBrowser.random_wait()
            if self.StealthBrowser.title != "":
                if self.handle_page(self.StealthBrowserrowser, expose_id):
                    self._debug_log(f"Attempt {attempt} succeeded!")
                    self.database.mark_expose_as_processed(expose_id)
                    self._debug_log(f"Expose {expose_id} marked as processed.")
                    return True
                else:
                    self._debug_log(f"Attempt {attempt} failed.")
            if attempt < max_attempts:
                self._debug_log("Retrying...\n")
                self.StealthBrowser.random_wait()
            else:
                self._debug_log(f"All attempts failed for expose ID {expose_id}.")
                self.database.increase_failures_count(expose_id)
                return False
