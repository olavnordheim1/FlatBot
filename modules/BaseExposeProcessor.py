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
    def __init__(self, email, password, application_text):
        self.name = "BaseProcessor"
        self.domain = "BaseDomain"
        self.email = email
        self.password = password
        self.application_text = application_text
        self.database = ExposeDB
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
    
    def extract_expose_link(email_body):
        raise NotImplementedError

    def _generate_expose_link(Expose):
        raise NotImplementedError
    

    #Returns updated Expose object
    def _handle_page(self, Expose, StealthBrowser):
        self._debug_log(self.name)
        raise NotImplementedError

    #Returns updated Expose object
    def process_expose(self, Expose):
        expose_id = Expose.expose_id
        offer_link = self.generate_offer_link(Expose)
        self._debug_log(f"Processing expose: {offer_link}")
        stealth_chrome = StealthBrowser()
        stealth_chrome.get(offer_link)
        stealth_chrome.load_cookies(self.name)
        stealth_chrome.random_wait()

        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            self._debug_log(f"Attempt {attempt}...")           

            if stealth_chrome.title != "":
                Expose, success = self._handle_page(Expose, stealth_chrome)
                if Expose.processed == True:
                    self._debug_log(f"Attempt {attempt} succeeded!")
                    return Expose, True
                else:
                    self._debug_log(f"Attempt {attempt} failed.")
            if attempt < max_attempts:
                self._debug_log("Retrying...\n")
                stealth_chrome.random_wait()
            else:
                self._debug_log(f"All attempts failed for expose ID {expose_id}.")
                Expose.failures += 1
                stealth_chrome.kill()
                return Expose, False
