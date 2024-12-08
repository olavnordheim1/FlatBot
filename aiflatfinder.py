from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time

print("Hello Selenium!")

immo_search_link = "https://www.immobilienscout24.de/Suche/shape/wohnung-mieten?shape=Y3V7fkhtYWFvQXBpQV97S3djQm10SnhuQWNfQGlAa2ZEb3VDcW1Ib1pjcURlZkBpYEZua0B5Z0x3YUFlZkNrdUNzbkJvfERsZEVxY0BwfUJ9U2ZvS2peYndCcmFCeHNBe1VqZEVxY0J4e0RoQGhDZnNAZGZDemRCYmhC&haspromotion=false&numberofrooms=1.5-&price=-1000.0&exclusioncriteria=swapflat&pricetype=calculatedtotalrent&enteredFrom=saved_search"

# Set up Chrome options
chrome_options = Options()
chrome_options.add_argument("--headless")  # Run in headless mode
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

# Initialize WebDriver
driver = webdriver.Chrome(options=chrome_options)
driver.get(immo_search_link)

# Wait and check title
time.sleep(5)
print("Done sleeping")
print("Page Title:", driver.title)

# Ensure page loaded correctly
assert "No results found." not in driver.page_source

# Close the driver
driver.close()
