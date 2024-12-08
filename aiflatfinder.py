from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import time

print("Hello Selenium!")
immo_search_link = "https://www.immobilienscout24.de/Suche/shape/wohnung-mieten?shape=Y3V7fkhtYWFvQXBpQV97S3djQm10SnhuQWNfQGlAa2ZEb3VDcW1Ib1pjcURlZkBpYEZua0B5Z0x3YUFlZkNrdUNzbkJvfERsZEVxY0BwfUJ9U2ZvS2peYndCcmFCeHNBe1VqZEVxY0J4e0RoQGhDZnNAZGZDemRCYmhC&haspromotion=false&numberofrooms=1.5-&price=-1000.0&exclusioncriteria=swapflat&pricetype=calculatedtotalrent&enteredFrom=saved_search"
#immo_serach_title = ""

driver = webdriver.Chrome()
driver.get(immo_search_link)
time.sleep(30)
print("done sleeping")
print (driver.title)


elem = driver.find_element(By.NAME, "q")
elem.clear()
assert "No results found." not in driver.page_source
driver.close()
