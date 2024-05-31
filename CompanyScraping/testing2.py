
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
time.sleep(5)
browser.quit()
