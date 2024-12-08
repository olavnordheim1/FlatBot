import os
import time
import json
import paramiko
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# SSH and file paths
SERVER_ADDRESS_SSH = os.getenv("SERVER_ADDRESS_SSH")
SSH_USERNAME = os.getenv("SSH_USERNAME")
REMOTE_COOKIE_PATH = os.getenv("REMOTE_COOKIE_PATH", "/home/username/cookies/cookies.json")
LOCAL_COOKIE_FILE = os.getenv("LOCAL_COOKIE_FILE", "./cookies.json")
LOGIN_URL = "https://www.immobilienscout24.de"

def retrieve_cookies():
    """Launches a headless Chrome browser, logs in, and saves cookies."""
    print("Starting headless browser...")
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(LOGIN_URL)
        print(f"Navigated to {LOGIN_URL}. Please log in...")

        # Give time for manual login
        input("Press Enter after completing login...")

        # Save cookies to file
        cookies = driver.get_cookies()
        with open(LOCAL_COOKIE_FILE, "w") as file:
            json.dump(cookies, file, indent=4)
        
        print(f"Cookies saved to {LOCAL_COOKIE_FILE}.")
        driver.quit()

    except Exception as e:
        print(f"Error retrieving cookies: {e}")

def transfer_cookie():
    """Transfers the cookie file to the remote server via SSH."""
    try:
        ssh = paramiko.SSHClient()
        ssh.load_system_host_keys()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        print(f"Connecting to {SERVER_ADDRESS_SSH} as {SSH_USERNAME}...")
        ssh.connect(SERVER_ADDRESS_SSH, username=SSH_USERNAME)

        sftp = ssh.open_sftp()
        print(f"Transferring {LOCAL_COOKIE_FILE} to {REMOTE_COOKIE_PATH}...")
        sftp.put(LOCAL_COOKIE_FILE, REMOTE_COOKIE_PATH)
        sftp.close()

        print("Cookies transferred successfully!")
        ssh.close()

    except FileNotFoundError:
        print(f"Error: {LOCAL_COOKIE_FILE} not found.")
    except Exception as e:
        print(f"Error during transfer: {e}")

if __name__ == "__main__":
    retrieve_cookies()
    transfer_cookie()
