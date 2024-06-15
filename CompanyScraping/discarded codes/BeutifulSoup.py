import requests
from bs4 import BeautifulSoup

# Make a request to the website
url = 'https://www.kompass.com/z/nl/r/north-brabant/nl_30/'
response = requests.get(url)

# Parse the HTML content
soup = BeautifulSoup(response.content, 'html.parser')

organization_names = soup.select('div.company-container')

for org in organization_names:
    # Assuming the organization name is in a <span> or <a> tag within the div
    title = org.find('title') or org.find('a')
    if title:
        print(title.text.strip())



# Navigate to the targetted HTML container
# body = soup.find('body', class_='classificationListCompany')
# dive deeper 
# and deeper
# main_div = soup.find('div', class_='main-div')




# Extract organization names from div in the homepage
#organization_names = []
#for div in soup.find_all('div', class_='col col-title company-container'):
    #organization_names.append(div.text.strip())

#target_data = soup.select_one('body.classificationListCompany main.main div.container div.nomenclature_wrapper div.resultatsListe div.container div.row section.resultants div.row div.prod_list div.company-container').text.strip()