#    time.sleep(5)

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
import time 

# Disable automation indicators on the browser
options = webdriver.ChromeOptions()
options.add_argument("--disable-blink-features=AutomationControlled") 
options.add_experimental_option("excludeSwitches", ["enable-automation"]) 
options.add_experimental_option("useAutomationExtension", False) 
# Initiate driver/browser with the set options above
browser = webdriver.Chrome(options=options) 
browser.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")


# Open broser to the specified page
browser.get("https://www.yelu.nl/location/s_Hertogenbosch")
time.sleep(30)
print("Searching through: " + browser.title)
# Wait for company listing to be present on the webpage
time.sleep(5)

# Searching for individual company listings
listings = browser.find_elements(By.CLASS_NAME, "company with_img g_0")
# Loop through each listing
for li in listings:
    # Search for name of company via link tags <a> 
    time.sleep(5)
    findName = li.find_element(By.TAG_NAME, "a")
    time.sleep(5)
    print("Comapany: " + findName.text)

browser.quit()
