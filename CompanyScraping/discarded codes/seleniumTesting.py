# https://testrigor.com/blog/selenium-with-python-cheat-sheet/

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time 


service = Service(excutable_path="chromedriver.exe")
browser = webdriver.Chrome(service=service)

# Open broser to the specified page
browser.get("https://www.kvk.nl/zoeken/")
time.sleep(5)

# Wait for input element(search bar) to be present on the webpage
WebDriverWait(browser, 5).until(
    EC.presence_of_element_located((By.TAG_NAME, "input"))
)

print("Searching through: " + browser.title)


inputElement = browser.find_element(By.TAG_NAME, "input")
inputElement.clear()
inputElement.send_keys("Eindhoven" + Keys.ENTER)

# Wait for button element to be present on the webpage
WebDriverWait(browser, 5).until(
    EC.presence_of_element_located((By.CSS_SELECTOR, "button[aria-label='Handelsregister']"))
)

button = browser.find_element(By.CSS_SELECTOR, "button[aria-label='Handelsregister']")
button.click()

# Wait for ul element to be present on the webpage
ulElement = WebDriverWait(browser, 5).until(
    EC.presence_of_element_located((By.TAG_NAME, "ul"))
)

# Find all <li> elements within the ul element
listElements = ulElement.find_elements(By.TAG_NAME, "li")
print("companies found:")

# Iterate over each <li> element
for li in listElements:
    # Find <a> elements within the current <li> element
    aElements = li.find_elements(By.TAG_NAME, "a")
    
    # Iterate over <a> elements within the current <li> element
    for a in aElements:
        # Extract and print the text of the <a> tag (title)
        print(a.text)


time.sleep(10)
print("Task Complete!")
browser.quit()


