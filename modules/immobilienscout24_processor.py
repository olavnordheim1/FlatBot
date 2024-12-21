
import os
import base64
import re
import logging
from modules.Expose import Expose
from modules.BaseExposeProcessor import BaseExposeProcessor
from modules.StealthBrowser import StealthBrowser
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class Immobilienscout24_processor(BaseExposeProcessor):
    name = "Immobilienscout24"
    domain = "immobilienscout24.de"

    def __init__(self, stealthbrowser):
   
        # Load environment variables
        load_dotenv()
        IMMO_EMAIL = base64.b64decode(os.getenv("IMMO_EMAIL")).decode("utf-8")
        IMMO_PASSWORD = base64.b64decode(os.getenv("IMMO_PASSWORD")).decode("utf-8")

        super().__init__(IMMO_EMAIL, IMMO_PASSWORD, stealthbrowser)

        self.immo_page_titles = {
            "captcha_wall": "Ich bin kein Roboter",
            "offer_expired": "Angebot nicht gefunden",
            "offer_deactivated": "Angebot wurde deaktiviert",
            "login_page": "Welcome - ImmobilienScout24",
            "error_page": "Fehler",
            "home_page": "ImmoScout24 – Die Nr. 1 für Immobilien"
        }

    @staticmethod
    def extract_expose_link(subject, email_body):
        #Extract unique expose links from the email body specific to Immobilienscout24#

    	# Filter Keywords
        subject_keywords = {"angebot", "offer"}

        # Normalize keywords to lowercase for consistent matching
        subject_keywords = {keyword.lower() for keyword in subject_keywords}

        # Check subject filter before processing
        subject_lower = subject.lower()
        if not any(keyword in subject_lower for keyword in subject_keywords):
            return []

        # Extract expose links using a regex pattern
        pattern = re.compile(r"https:\/\/[a-zA-Z0-9./?=&_-]*expose/(\d+)")
        return list(set(pattern.findall(email_body)))
    
    @staticmethod
    def _generate_expose_link(Expose):
        offer_link = f"https://push.search.is24.de/email/expose/{Expose.expose_id}"
        return offer_link

    #Returns updated Expose object, called in process_expose
    def _handle_page(self, Expose):
        page_title = self.stealth_chrome.title
        logger.info(f"Page title: {page_title}")
        
        if self.immo_page_titles['captcha_wall'] in page_title:
            self._handle_captcha()
            return Expose, False
        elif self.immo_page_titles['offer_expired'] in page_title or self.immo_page_titles['offer_deactivated'] in page_title:
            logger.info("Offer expired or deactivated, skipping.")
            Expose.processed = True
            logger.info(f"Expose {Expose.expose_id} marked as processed.")
            return Expose, False
        elif self.immo_page_titles['login_page'] in page_title:
            logger.warning("Login page detected, attempting login.")
            self._perform_login()
        elif self.immo_page_titles['error_page'] in page_title or self.immo_page_titles['home_page'] in page_title:
            logger.warning("Error or landed on home page, skipping.")
            return Expose, False
        self.stealth_chrome.perform_random_action()
        self._accept_cookies()
        # Could be a good offer, let´s check
        #Can we scrape it?
        Expose, scraped = self._scrape_expose(Expose)
        if not scraped:
            return Expose, False

        # Are we logged in?
        if not self._check_login():
            self._perform_login()
            return Expose, False
        
        # Can we apply?
        self._accept_cookies()
        Expose, applied = self._apply_for_offer(Expose)
        if not applied:
            return Expose, False      
        return Expose, True

    ###############################
    ####### IMMO FUNCTIONS ########
    ###############################
    
    def _check_login(self):
        # Check login status based on page elements
        try:
            login_header = self.stealth_chrome.find_element(By.CLASS_NAME, "topnavigation__sso-login__header")
            if login_header and "angemeldet als" in login_header.text:
                logger.info("User already logged in.")
                return True
        except Exception:
            logger.info("User does not seems to be logged in")
            return False
        
    def _perform_login(self):
        self.stealth_chrome.dismiss_overlays()
        try:
            login_link = self.stealth_chrome.find_element(By.CLASS_NAME, "topnavigation__sso-login__middle")
            if login_link and "Anmelden" in login_link.text:
                logger.info("User not logged in. Attempting login.")
                login_link.click()
                try:
                    StealthBrowser.random_wait()
                    email_field = WebDriverWait(self.stealth_chrome, 10).until(
                        EC.presence_of_element_located((By.ID, "username"))
                    )
                    self.stealth_chrome.send_keys_human_like(email_field, self.email)
                    logger.info("Email entered successfully.")
                    self.stealth_chrome.perform_random_action()

                    submit_button = WebDriverWait(self.stealth_chrome, 10).until(
                        EC.presence_of_element_located((By.ID, "submit"))
                    )
                    self.stealth_chrome.random_mouse_movements(submit_button)
                    self.stealth_chrome.dismiss_overlays()
                    submit_button.click()
                    logger.info("Email submission successful, waiting for password field.")

                    StealthBrowser.random_wait()
                    password_field = WebDriverWait(self.stealth_chrome, 10).until(
                        EC.presence_of_element_located((By.ID, "password"))
                    )
                    self.stealth_chrome.send_keys_human_like(password_field, self.password)
                    logger.info("Password entered successfully.")
                    self.stealth_chrome.perform_random_action()

                    remember_me_checkbox = WebDriverWait(self.stealth_chrome, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "label[for='rememberMeCheckBox']"))
                    )
                    self.stealth_chrome.random_mouse_movements(remember_me_checkbox)
                    #remember_me_checkbox.click()
                    #logger.info("'Remember Me' checkbox selected.")
                    self.stealth_chrome.perform_random_action()
                    login_button = WebDriverWait(self.stealth_chrome, 10).until(
                        EC.presence_of_element_located((By.ID, "loginOrRegistration"))
                    )
                    self.stealth_chrome.random_mouse_movements(login_button)
                    self.stealth_chrome.dismiss_overlays()
                    login_button.click()
                    logger.info("Login submitted successfully.")
                    StealthBrowser.random_wait(5,10)

                    ## TO-DO validate success

                    self.stealth_chrome.save_cookies(self.name)
                    #self.stealth_chrome.refresh()
                    logger.info("Page reloaded after login.")
                    return True
                except Exception as e:
                    logger.warning("Login failed.", e)
                    #self.stealth_chrome_helpers.wait_for_user()
                    # TO-DO Notify user
                    return False                           
        except Exception:
            logger.info("Login button not found.", e)
            #self.stealth_chrome_helpers.wait_for_user()
            # TO-DO Notify user
            return False
        

    def _scrape_expose(self, Expose):
        # Check title
        try:
            offer_title = self.stealth_chrome.safe_find_element(By.ID, "expose-title")

            if offer_title != "Unknown":
                logger.info("Found Offer title, scriping the rest.")
                Expose.location = self.stealth_chrome.safe_find_element(By.CLASS_NAME, "zip-region-and-country")
                Expose.agent_name = self.stealth_chrome.safe_find_element(By.CLASS_NAME, "truncateChild_5TDve")
                Expose.real_estate_agency = self.stealth_chrome.safe_find_element(By.CSS_SELECTOR, "p[data-qa='company-name']")
                Expose.price_kalt = self.stealth_chrome.safe_find_element(By.CLASS_NAME, "is24-preis-value")
                Expose.square_meters = self.stealth_chrome.safe_find_element(By.CLASS_NAME, "is24qa-wohnflaeche-main")
                Expose.number_of_rooms = self.stealth_chrome.safe_find_element(By.CLASS_NAME, "is24qa-zi-main")
                Expose.nebekosten = self.stealth_chrome.safe_find_element(By.CLASS_NAME, "is24qa-nebenkosten")
                Expose.price_warm = self.stealth_chrome.safe_find_element(By.CSS_SELECTOR, "dd.is24qa-gesamtmiete")
                Expose.construction_year = self.stealth_chrome.safe_find_element(By.CLASS_NAME, "is24qa-baujahr")
                Expose.description = self.stealth_chrome.safe_find_element(By.CLASS_NAME, "is24qa-objektbeschreibung")
                Expose.neighborhood = self.stealth_chrome.safe_find_element(By.CLASS_NAME, "is24qa-lage")
                
                logger.info(f"Expose {Expose.expose_id} scraped to database.")
                self.stealth_chrome.perform_random_action()
                return Expose, True
            
        except Exception:
            logger.warning("Not valid offer title found, bad attempt!")
            return Expose, False
        

    def _apply_for_offer(self, Expose):
        logger.info("Trying application...")
        try:
            message_button = WebDriverWait(self.stealth_chrome, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "Button_button-primary__6QTnx"))
            )
            self.stealth_chrome.dismiss_overlays()
            message_button.click()
            logger.info("Message button found and clicked successfully.")
        except Exception as e:
            logger.info("Failed to find or click message button.")
            return Expose, False

        self.stealth_chrome.perform_random_action()

        if "Welcome - ImmobilienScout24" in self.stealth_chrome.title:
            logger.info("User not logged in. Bad attempt")
            return Expose, False

        if "MieterPlus freischalten | ImmoScout24" in self.stealth_chrome.title:
            logger.info("MieterPlus page detected. Skipping expose.")
            # moved in process_expose
            #database.mark_expose_as_processed(expose_id)
            logger.info(f"Expose {Expose.expose_id} marked as processed.")
            Expose.processed = True
            return Expose, True

        try:
            StealthBrowser.random_wait()
            message_label = WebDriverWait(self.stealth_chrome, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "label[for='message']"))
            )
            message_box = self.stealth_chrome.find_element(By.ID, "message")
            message_box.clear()
        except:
            logger.warning("Message pop-up did not open or message box not found, bad attempt")
            return Expose, False

        self._fill_application_form(Expose)
        logger.info("Application text entered successfully.")

        self.stealth_chrome.perform_random_action()
        try:
            send_button = WebDriverWait(self.stealth_chrome, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "button[type='submit'].Button_button-primary__6QTnx"))
            )
            self.stealth_chrome.execute_script("arguments[0].scrollIntoView(true);", send_button)
            self.stealth_chrome.dismiss_overlays()
            send_button.click()
            logger.info("Submit clicked, waiting for confirmation.")
        except:
            logger.info("Submit not fount!")
            return Expose, False

        confirmation_message = WebDriverWait(self.stealth_chrome, 10).until(
            EC.presence_of_element_located((By.XPATH, "//h2[text()='Nachricht gesendet']"))
        )
        if confirmation_message:
            # moved in process_expose
            #database.mark_expose_as_processed(expose_id)
            logger.info(f"Expose {Expose.expose_id} applied succesfully.")
            Expose.processed = True
            # TO-DO Notify user?
            return Expose, True
        else:
            # TO-DO Handle unfilled form fields
            logger.warning("Failed to send message or fill the form.", e)
            return Expose, False

    def _fill_application_form(self, Expose):
        self.stealth_chrome.dismiss_overlays()

        form_values = [
            ("vonplz", "text", os.getenv("APPLICANT_POST_CODE")),
            ("nachplz", "text", ""),
            ("message", "textarea", self.ApplicationGenerator.generate_application(Expose)),
            ("salutation", "text", os.getenv("APPLICANT_SALUTATION")),
            ("salutation", "select", os.getenv("APPLICANT_SALUTATION")),
            ("firstName", "text", os.getenv("APPLICANT_NAME")),
            ("lastName", "text", os.getenv("APPLICANT_SURNAME")),
            ("phoneNumber", "tel", os.getenv("APPLICANT_PHONE")),
            ("phoneNumber", "text",  os.getenv("APPLICANT_PHONE")),
            ("phoneNumber", "number",  os.getenv("APPLICANT_PHONE")),
            ("emailAddress", "email",  os.getenv("APPLICANT_EMAIL")),
            ("emailAddress", "text",  os.getenv("APPLICANT_EMAIL")),
            ("street", "text", os.getenv("APPLICANT_STREET")),
            ("houseNumber", "text", os.getenv("APPLICANT_HOUSE_NUM")),
            ("postcode", "text", os.getenv("APPLICANT_POST_CODE")),
            ("city", "text", os.getenv("APPLICANT_CITY")),
            ("moveInDateType", "text", os.getenv("APPLICANT_MOVEIN_DATE_TYPE")),
            ("moveInDateType", "select", os.getenv("APPLICANT_MOVEIN_DATE_TYPE")),
            ("numberOfPersons", "text", os.getenv("APPLICANT_NUM_PERSONS")),
            ("numberOfPersons", "select", os.getenv("APPLICANT_NUM_PERSONS")),
            ("employmentRelationship", "text", os.getenv("APPLICANT_EMPLOYEMENT_RELATIONSHIP")),
            ("employmentRelationship", "select", os.getenv("APPLICANT_EMPLOYEMENT_RELATIONSHIP")),
            ("employmentStatus", "select",  os.getenv("APPLICANT_EMPLOYEMENT_STATUS")),
            ("employmentStatus", "text",  os.getenv("APPLICANT_EMPLOYEMENT_STATUS")),
            ("income", "select", os.getenv("APPLICANT_INCOME_RANGE")),
            ("incomeAmount", "tel", os.getenv("APPLICANT_INCOME_AMMOUNT")),
            ("incomeAmount", "text", os.getenv("APPLICANT_INCOME_AMMOUNT")),
            ("incomeAmount", "number", os.getenv("APPLICANT_INCOME_AMMOUNT")),
            ("applicationPackageCompleted", "text", os.getenv("APPLICANT_DOCUMENTS_AVAILABLE")),
            ("applicationPackageCompleted", "select", os.getenv("APPLICANT_DOCUMENTS_AVAILABLE")),
            ("hasPets", "text", os.getenv("APPLICANT_HAS_PETS")),
            ("hasPets", "select", os.getenv("APPLICANT_HAS_PETS")),
            ("sendUser", "checkbox", os.getenv("APPLICANT_SEND_PROFILE")),
            ("sendUserProfile", "checkbox", os.getenv("APPLICANT_SEND_PROFILE")),
            ("numberOfAdults", "number", os.getenv("APPLICANT_NUM_ADULTS")),
            ("numberOfAdults", "tel", os.getenv("APPLICANT_NUM_ADULTS")),
            ("numberOfKids", "number",  os.getenv("APPLICANT_NUM_KIDS")),
            ("numberOfKids", "tel", os.getenv("APPLICANT_NUM_KIDS")),
            ("isRelocationOfferChecked", "checkbox", "false"),
            ("rentArrears", "select", os.getenv("APPLICANT_RENT_ARREARS")),
            ("insolvencyProcess", "select", os.getenv("APPLICANT_INSOLVENCY_PROCESS")),
        ]

        # Scroll and dynamically load all form fields
        self.stealth_chrome.scroll_to_bottom()
        fields = self.stealth_chrome.find_elements(By.TAG_NAME, "input") + \
                self.stealth_chrome.find_elements(By.TAG_NAME, "textarea") + \
                self.stealth_chrome.find_elements(By.TAG_NAME, "select")

        # Ignore hidden fields
        visible_fields = []
        for field in fields:
            field_type_attr = field.get_attribute("type")
            # Determine field_type properly
            if field.tag_name.lower() == "select":
                field_type = "select"
            else:
                field_type = field_type_attr.lower() if field_type_attr else field.tag_name.lower()

            # Skip hidden fields
            if field_type == "hidden":
                continue

            visible_fields.append(field)

        # Print all found (visible) fields once
        for field in visible_fields:
            field_name = field.get_attribute("name")
            if field.tag_name.lower() == "select":
                # For selects, we've standardized the type as "select"
                field_type = "select"
            else:
                field_type_attr = field.get_attribute("type")
                field_type = field_type_attr.lower() if field_type_attr else field.tag_name.lower()
            logging.info(f"Found field: name={field_name}, type={field_type}")

        # Iterate through fields and match with provided values
        for field in visible_fields:
            field_name = field.get_attribute("name")
            if field.tag_name.lower() == "select":
                field_type = "select"
            else:
                field_type_attr = field.get_attribute("type")
                field_type = field_type_attr.lower() if field_type_attr else field.tag_name.lower()

            for name, expected_type, value in form_values:
                if field_name == name and field_type == expected_type:
                    try:                        
                        # Simulate human-like mouse movements
                        self.stealth_chrome.random_mouse_movements(field)

                        # Fill the field based on its type
                        if field_type in ["text", "email", "tel", "number"] or field.tag_name == "textarea":
                            field.clear()
                            self.stealth_chrome.send_keys_human_like(field, value)
                            StealthBrowser.random_wait()
                        elif field_type == "select":
                            Select(field).select_by_visible_text(value)
                            StealthBrowser.random_wait()
                        elif field_type == "checkbox":
                            current_state = field.is_selected()
                            if value.lower() in ["true", "yes", "1"] and not current_state:
                                field.click()
                            elif value.lower() in ["false", "no", "0"] and current_state:
                                field.click()
                            StealthBrowser.random_wait()
                    except Exception as e:
                        logging.info(f"Could not fill field '{field_name}': {e}")

        # Recheck for dynamically loaded fields (but do not print them again)
        self.stealth_chrome.scroll_to_bottom()
        additional_fields = self.stealth_chrome.find_elements(By.TAG_NAME, "input") + \
                            self.stealth_chrome.find_elements(By.TAG_NAME, "textarea") + \
                            self.stealth_chrome.find_elements(By.TAG_NAME, "select")

        # No printing here to ensure fields are printed only once
        for field in additional_fields:
            pass  # Just pass without logging

        logging.info("Form filling completed.")

    def _accept_cookies(self):
        try:
            shadow_root = self.stealth_chrome.find_element(By.CSS_SELECTOR, "#usercentrics-root").shadow_root
            button = shadow_root.find_element(By.CSS_SELECTOR, "button[data-testid='uc-accept-all-button']")
            self.stealth_chrome.random_mouse_movements(button)
            button.click()
            logging.info("Successfully clicked the 'Accept All' button.")
        except:
            logging.info("Failed to click the 'Accept All' button")

    def _handle_captcha(self):
        logger.warning("Captcha detected.")
        logger.info("Trying show challenge")

        try:
            shadow_root = self.stealth_chrome.find_element(By.CSS_SELECTOR, "#captcha-container > awswaf-captcha").shadow_root ##captcha-container > awswaf-captcha
            try:
                button = shadow_root.find_element(By.CSS_SELECTOR, "#reqBtn")
                self.stealth_chrome.random_mouse_movements(button)
                button.click()
                logging.info("Successfully clicked show captcha.")
            except:
                logging.info("Failed to find show captcha")
            logging.info("Loading solver")

        except:
            logging.warning("Failed to find shadow root")

        # Wait for the element to be clickable using its XPath
        #wait = WebDriverWait(self.stealth_chrome, 10)
        #wait.until(EC.frame_to_be_available_and_switch_to_it((By.XPATH, "iframe xpath")))
        #click_to_verify = wd.find_element_by_xpath('//*[@id="1e505deed3832c02c96ca5abe70df9ab"]/div')
        #click_to_verify.click()
        #button = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@id='reqBtn']")))
        # Click the button
        #button.click()

        
        #self.stealth_chrome.dismiss_overlays()
        StealthBrowser.random_wait(1,3)
        self.stealth_chrome.wait_for_user()
