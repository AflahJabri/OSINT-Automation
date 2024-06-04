import time
import random
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import psycopg2
from psycopg2 import sql
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Function to scrape business listings from a given base URL
def get_business_list(base_url, max_pages=100, delay=1):
    businesses = []
    seen_business_ids = set()

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(service=Service(), options=chrome_options)
    driver.get(base_url)
    time.sleep(delay + random.uniform(0, delay))

    for page in range(1, max_pages + 1):
        print(f"Scraping page {page}")

        time.sleep(delay + random.uniform(0, delay))
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        business_elements = soup.select('div.company.with_img.g_0, div.company.g_0')

        if not business_elements:
            print(f"No more business listings found at page {page}")
            break

        for business in business_elements:
            name = business.find('h4').text.strip()
            address = business.find('div', class_='address').text.strip()
            link_tag = business.find('a')
            company_url, phone = None, None
            if link_tag and 'href' in link_tag.attrs:
                company_page_url = link_tag['href']
                company_url, phone = get_company_details(company_page_url)

            business_id = f"{name}_{address}"

            if business_id not in seen_business_ids:
                seen_business_ids.add(business_id)
                businesses.append({'name': name, 'address': address, 'url': company_url, 'phone': phone})
            else:
                print(f"Duplicate listing found: {name}, {address}")

        print(f"Page {page}: Total unique businesses added: {len(businesses)}")

        try:
            next_button = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//a[@rel="next"]'))
            )
            driver.execute_script("arguments[0].click();", next_button)
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div.company.with_img.g_0, div.company.g_0'))
            )
            time.sleep(delay + random.uniform(0, delay))
        except TimeoutException:
            print("Timeout waiting for page to load or unable to find next button")
            break
        except NoSuchElementException:
            print("No more pages available or unable to find next button")
            break
        except StaleElementReferenceException:
            print("Stale element reference, retrying...")
            time.sleep(delay)
            driver.get(driver.current_url)
            continue

    driver.quit()
    return businesses

# Function to fetch the company's URL and phone from its page
def get_company_details(company_page_url):
    base_url = 'https://www.yelu.nl'
    url = f"{base_url}{company_page_url}"
    print(f"Fetching company details from: {url}")

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Failed to retrieve company page: Status code {response.status_code}")
            return None, None

        soup = BeautifulSoup(response.content, 'html.parser')
        website_tag = soup.find('div', class_='text weblinks').find('a')
        phone_tag = soup.find('div', class_='text phone')

        website_url = website_tag['href'] if website_tag and 'href' in website_tag.attrs else None
        phone = phone_tag.text.strip() if phone_tag else None

        return website_url, phone
        
    except Exception as e:
        print(f"Error fetching company details: {e}")
        return None, None

# Function to save the scraped data to PostgreSQL
def save_to_postgresql(businesses):
    try:
        conn = psycopg2.connect(
            dbname="postgres",
            user="postgres",
            password="password",
            host="localhost",
            port="5432"
        )
        cursor = conn.cursor()

        for business in businesses:
            cursor.execute(
                sql.SQL("INSERT INTO companies (name, address, url, phone) VALUES (%s, %s, %s, %s) ON CONFLICT (name, address) DO NOTHING"),
                [business['name'], business['address'], business['url'], business['phone']]
            )

        conn.commit()
        cursor.close()
        conn.close()
        print("Data saved successfully to PostgreSQL")

    except Exception as e:
        print(f"Error: {e}")

def scrape_and_save(base_urls, max_pages=2, delay=1):
    for base_url in base_urls:
        print(f"Processing URL: {base_url}")
        business_list = get_business_list(base_url, max_pages, delay)
        save_to_postgresql(business_list)

# List of URLs to scrape
base_urls = [
'https://www.yelu.nl/location/s_Hertogenbosch',
'https://www.yelu.nl/location/Oss',
'https://www.yelu.nl/location/Oisterwijk',
'https://www.yelu.nl/location/Waalwijk',
'https://www.yelu.nl/location/Grave',
'https://www.yelu.nl/location/Heusden',
'https://www.yelu.nl/location/Bergeijk',
'https://www.yelu.nl/location/Bergen_op_Zoom',
'https://www.yelu.nl/location/Bladel',
'https://www.yelu.nl/location/Boxmeer',
'https://www.yelu.nl/location/Boxtel',
'https://www.yelu.nl/location/Best',
'https://www.yelu.nl/location/Breda',
'https://www.yelu.nl/location/Cuijk',
'https://www.yelu.nl/location/Deurne',
'https://www.yelu.nl/location/Dongen',
'https://www.yelu.nl/location/Drimmelen',
'https://www.yelu.nl/location/Eersel',
'https://www.yelu.nl/location/Eindhoven',
'https://www.yelu.nl/location/Etten_leur',
'https://www.yelu.nl/location/Geertruidenberg',
'https://www.yelu.nl/location/Geldrop',
'https://www.yelu.nl/location/Gemert_bakel',
'https://www.yelu.nl/location/Goirle',
'https://www.yelu.nl/location/Helmond',
'https://www.yelu.nl/location/Heusden',
'https://www.yelu.nl/location/Loon_op_zand',
'https://www.yelu.nl/location/Moerdijk',
'https://www.yelu.nl/location/Nuenen',
'https://www.yelu.nl/location/Oirschot',
'https://www.yelu.nl/location/Oisterwijk',
'https://www.yelu.nl/location/Oosterhout',
'https://www.yelu.nl/location/Roosendaal',
'https://www.yelu.nl/location/Rucphen',
'https://www.yelu.nl/location/Schijndel',
'https://www.yelu.nl/location/Sint_michielsgestel',
'https://www.yelu.nl/location/Sint_oedenrode',
'https://www.yelu.nl/location/Someren',
'https://www.yelu.nl/location/Steenbergen',
'https://www.yelu.nl/location/Tilburg',
'https://www.yelu.nl/location/Uden',
'https://www.yelu.nl/location/Valkenswaard',
'https://www.yelu.nl/location/Veghel',
'https://www.yelu.nl/location/Veldhoven',
'https://www.yelu.nl/location/Vught',
'https://www.yelu.nl/location/Waalwijk',
'https://www.yelu.nl/location/Werkendam',
'https://www.yelu.nl/location/Woensdrecht',
'https://www.yelu.nl/location/Woudrichem',
'https://www.yelu.nl/location/Zundert'
]

# Execute the scraping and saving process
scrape_and_save(base_urls, max_pages=1, delay=1)









# List of cities in North Brabant and the number of companies in thousands:

# https://www.yelu.nl/location/s_Hertogenbosch 4.48
# https://www.yelu.nl/location/Oss 3.20
# https://www.yelu.nl/location/Oisterwijk 1.36
# https://www.yelu.nl/location/Waalwijk 2.23
# https://www.yelu.nl/location/Grave 0.34
# https://www.yelu.nl/location/Heusden 0.06
# https://www.yelu.nl/location/Bergeijk 0.78
# https://www.yelu.nl/location/Bergen_op_Zoom 2.51
# https://www.yelu.nl/location/Bladel 0.79
# https://www.yelu.nl/location/Boxmeer 0.65
# https://www.yelu.nl/location/Boxtel 1.32
# https://www.yelu.nl/location/Best 1.68
# https://www.yelu.nl/location/Breda 8.9
# https://www.yelu.nl/location/Cuijk 0.97
# https://www.yelu.nl/location/Deurne 1.44
# https://www.yelu.nl/location/Dongen 1.17
# https://www.yelu.nl/location/Drimmelen 0.73
# https://www.yelu.nl/location/Eersel 0.72
# https://www.yelu.nl/location/Eindhoven 11.75
# https://www.yelu.nl/location/Etten_leur 2.27
# https://www.yelu.nl/location/Geertruidenberg 0.26
# https://www.yelu.nl/location/Geldrop 1.39
# https://www.yelu.nl/location/Gemert_bakel 0.002
# https://www.yelu.nl/location/Goirle 0.96
# https://www.yelu.nl/location/Helmond 4.34
# https://www.yelu.nl/location/Heusden 0.06
# https://www.yelu.nl/location/Loon_op_zand 0.30
# https://www.yelu.nl/location/Moerdijk 0.32
# https://www.yelu.nl/location/Nuenen 1.48
# https://www.yelu.nl/location/Oirschot 0.83
# https://www.yelu.nl/location/Oisterwijk 1.36
# https://www.yelu.nl/location/Oosterhout 2.38
# https://www.yelu.nl/location/Roosendaal 3.49
# https://www.yelu.nl/location/Rucphen 0.28
# https://www.yelu.nl/location/Schijndel 1.45
# https://www.yelu.nl/location/Sint_michielsgestel 0.57
# https://www.yelu.nl/location/Sint_oedenrode 0.93
# https://www.yelu.nl/location/Someren 1.07
# https://www.yelu.nl/location/Steenbergen 0.006
# https://www.yelu.nl/location/Tilburg 8.52
# https://www.yelu.nl/location/Uden 2.29
# https://www.yelu.nl/location/Valkenswaard 1.98
# https://www.yelu.nl/location/Veghel 1.92
# https://www.yelu.nl/location/Veldhoven 2.19
# https://www.yelu.nl/location/Vught 1.43
# https://www.yelu.nl/location/Waalwijk 2.23
# https://www.yelu.nl/location/Werkendam 0.98
# https://www.yelu.nl/location/Woensdrecht 0.07
# https://www.yelu.nl/location/Woudrichem 0.21
# https://www.yelu.nl/location/Zundert 0.67

# estimated total number of companies = 91,318 