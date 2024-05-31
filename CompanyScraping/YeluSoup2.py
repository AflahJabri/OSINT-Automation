import requests
from bs4 import BeautifulSoup
import time
import random

def get_business_list(baseURL, max_pages=100, delay=1):
    businesses = []
    
    for page in range(1, max_pages + 1):
        url = f"{baseURL}/{page}"
        response = requests.get(url)
        
        # Check if the page was retrieved successfully
        if response.status_code != 200:
            print(f"Failed to retrieve page {page}")
            break
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        business_elements = soup.find_all('div', class_='company with_img g_0')
        
        # If no business listings are found, assume we've reached the last page
        if not business_elements:
            print(f"No more business listings found at page {page}")
            break
        
        for business in business_elements:
            name = business.find('h4').text.strip()
            address = business.find('div', class_='address').text.strip()
            businesses.append({'name': name, 'address': address})
        
        # Add delay between requests
        time.sleep(delay + random.uniform(0, delay))
    
    return businesses

# Example usage
baseURL = 'https://www.yelu.nl/location/s_Hertogenbosch'
business_list = get_business_list(baseURL, delay=3)  

for business in business_list:
    print(business)
