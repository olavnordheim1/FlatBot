from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
from twocaptcha import TwoCaptcha


class RecaptchaV2Solver():
    
    # CONFIGURATION
    url = "https://2captcha.com/demo/recaptcha-v2"
    apikey = os.getenv('2CAPTCHA_API_KEY')

    def __init__(self,
                sitekey_locator = "//div[@id='g-recaptcha']",
                submit_button_captcha_locator = "//button[@data-action='demo_action']",
                success_message_locator = "//p[contains(@class,'successMessage')]"):
        self.browser = browser
        # LOCATORS
        self.sitekey_locator = sitekey_locator
        self.submit_button_captcha_locator = submit_button_captcha_locator
        self.success_message_locator = success_message_locator


    # GETTERS

    def _get_element(locator):
        """Waits for an element to be clickable and returns it"""
        return WebDriverWait(browser, 30).until(EC.element_to_be_clickable((By.XPATH, locator)))


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
        print(f"Sitekey received: {sitekey}")
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
            print(f"Captcha solved")
            return result['code']
        except Exception as e:
            print(f"An error occurred: {e}")
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
        print("Token sent")

    def _click_check_button(self, locator):
        """
        Clicks the captcha check button.

        Args:
            locator (str): The XPath locator of the check button.
        """
        self._get_element(locator).click()
        print("Pressed the Check button")

    def _final_message(self, locator):
        """
        Retrieves and prints the final success message.

        Args:
            locator (str): The XPath locator of the success message.
        """
        message = self._get_element(locator).text
        print(message)

    # MAIN LOGIC
    def solve_captcha(self, url):
        with self.browser as browser:
            # Go to the specified URL
            browser.get(url)
            print('Started')

            # Getting sitekey from the sitekey element
            sitekey = self._get_sitekey(self.sitekey_locator)

            # Solving the captcha and receiving a token
            token = self._solver_captcha(self.apikey, sitekey, url)

            if token:
                # Sending solved captcha token
                self._send_token(token)

                # Pressing the Check button
                self._click_check_button(self.submit_button_captcha_locator)

                # Receiving and displaying a success message
                self._final_message(self.success_message_locator)

                browser.implicitly_wait(5)
                print("Finished")
            else:
                print("Failed to solve captcha")