import requests
from bs4 import BeautifulSoup

def get_business_list(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    businesses = []
    for business in soup.find_all('div', class_='company with_img g_0'):
        name = business.find('h4').text
        address = business.find('div', class_='address').text
        businesses.append({'name': name, 'address': address})
    
    return businesses

# Example usage
url = 'https://www.yelu.nl/location/s_Hertogenbosch'
business_list = get_business_list(url)
print(business_list)
