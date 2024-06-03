# https://testrigor.com/blog/selenium-with-python-cheat-sheet/

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
    # click on link and go the company specific page
    findLink.click()
    findkvk = browser.find_element(By.XPATH, "//th[text()='KvK nummer']/following-sibling::td")
    kvkNumber = findkvk.text
    browser.back()
    try:
        # Search for <div> containing company URL
        findWebsite = li.find_element(By.CLASS_NAME, "companyWeb")
        url = findWebsite.find_element(By.TAG_NAME, "a")
        print("Comapany: " + findLink.text,"with KvK number: " + kvkNumber + " with URL: " + url.get_attribute('href'))
    # An expection to handle crashes incase a comany has no website  
    except NoSuchElementException:
        print("Company: " + findLink.text + "with KvK number: " + kvkNumber + " but has no website.")


## Once done with the loop try clicking on next page, wait for 5 seconds and repeat loop
time.sleep(10)
print("Search Complete...")
browser.quit()
