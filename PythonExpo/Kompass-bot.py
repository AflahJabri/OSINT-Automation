# https://testrigor.com/blog/selenium-with-python-cheat-sheet/

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
import time 

service = Service(excutable_path="chromedriver.exe")
browser = webdriver.Chrome(service=service)

# Open broser to the specified page
browser.get("https://www.kompass.com/z/nl/r/north-brabant/nl_30/")
time.sleep(10)
print("Searching through: " + browser.title)

# Wait for company listing to be present on the webpage
listElement = WebDriverWait(browser, 5).until(
    EC.presence_of_element_located((By.ID, "resultatDivId"))
)

# Searching for individual company listings
listings = browser.find_elements(By.CLASS_NAME, "product-list-data")

# Loop through each listing
for li in listings:
    # Search for name of company via link tags <a> 
    findLink = li.find_element(By.TAG_NAME, "a")
    try:
        # Search for <div> containing company URL
        findWebsite = li.find_element(By.CLASS_NAME, "companyWeb")
        url = findWebsite.find_element(By.TAG_NAME, "a")
        print("Comapany: " + findLink.text, "  URL: " + url.get_attribute('href'))  
    except NoSuchElementException:
        print("Company: " + findLink.text + " has no website.")


## once done with the loop try clicking on next page, wait for 5 seconds and repeat loop
time.sleep(10)
print("Search Complete...")
browser.quit()


