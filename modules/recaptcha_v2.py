from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import logging
from twocaptcha import TwoCaptcha
from modules.StealthBrowser import StealthBrowser
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class RecaptchaV2Solver():
    
    # CONFIGURATION
    load_dotenv()
    url = "https://2captcha.com/demo/recaptcha-v2"
    apikey = os.getenv('2CAPTCHA_API_KEY')

    def __init__(self, browser : StealthBrowser):
        self.browser = browser
        pass


    # GETTERS

    def _get_element(self, locator):
        """Waits for an element to be clickable and returns it"""
        return WebDriverWait(self.browser, 30).until(EC.element_to_be_clickable((By.XPATH, locator)))


    # ACTIONS

    def _get_sitekey(self, locator):
        """
        Extracts the sitekey from the specified element.

        Args:
            locator (str): The XPath locator of the element.
        Returns:
            str: The sitekey value.
        """
        sitekey_element = self._get_element(locator)
        sitekey = sitekey_element.get_attribute('data-sitekey')
        logging.info(f"Sitekey received: {sitekey}")
        return sitekey

    def _solver_captcha(slef, apikey, sitekey, url):
        """
        Solves the reCaptcha using the 2Captcha service.

        Args:
            apikey (str): The 2Captcha API key.
            sitekey (str): The sitekey for the captcha.
            url (str): The URL where the captcha is located.
        Returns:
            str: The solved captcha code.
        """
        solver = TwoCaptcha(apikey)
        try:
            result = solver.recaptcha(sitekey=sitekey, url=url)
            logging.info(f"Captcha solved")
            return result['code']
        except Exception as e:
            logging.info(f"An error occurred: {e}")
            return None

    def _send_token(self, captcha_token):
        """
        Sends the captcha token to the reCaptcha response field.

        Args:
            captcha_token (str): The solved captcha token.
            """
        script = f"""
            document.querySelector('[id="g-recaptcha-response"]').innerText = '{captcha_token}';
        """
        self.browser.execute_script(script)
        logging.info("Token sent")

    def _click_check_button(self, locator):
        """
        Clicks the captcha check button.

        Args:
            locator (str): The XPath locator of the check button.
        """
        self._get_element(locator).click()
        logging.info("Pressed the Check button")

    def _final_message(self, locator):
        """
        Retrieves and prints the final success message.

        Args:
            locator (str): The XPath locator of the success message.
        """
        message = self._get_element(locator).text
        logging.info(message)

    # MAIN LOGIC
    def solve_captcha(self,
                      sitekey_locator = "//div[@id='g-recaptcha']",
                      submit_button_captcha_locator = "//button[@data-action='demo_action']",
                      success_message_locator = "//p[contains(@class,'successMessage')]"):
        with self.browser as browser:
            # Go to the specified URL
            #browser.get(url)
            logging.info('RecaptchaV2Solver Started')
            url = browser.current_url
            logging.info(f"Solving captcha url: {url}")
            # Getting sitekey from the sitekey element
            sitekey = self._get_sitekey(sitekey_locator)

            # Solving the captcha and receiving a token
            token = self._solver_captcha(self.apikey, sitekey, url)

            if token:
                # Sending solved captcha token
                self._send_token(token)

                # Pressing the Check button
                self._click_check_button(submit_button_captcha_locator)

                # Receiving and displaying a success message
                self._final_message(success_message_locator)

                browser.implicitly_wait(5)
                logging.info("Finished")
            else:
                logging.info("Failed to solve captcha")