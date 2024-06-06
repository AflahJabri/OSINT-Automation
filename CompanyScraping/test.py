import requests
import re

url = "https://kompassapi.shinystat.com/cgi-bin/kimpress.cgi?company=NLC9987504,NLC9987242"

try:
    response = requests.get(url)
    response.raise_for_status()
    content_type = response.headers.get('Content-Type')

    if 'application/json' in content_type:
        data = response.json()
        print(data)
    else:
        print("Response content is not in JSON format")
        content = response.text
        # Example of extracting a variable from JavaScript content
        match = re.search(r'var kimp="(.*?)";', content)
        if match:
            kimp_value = match.group(1)
            print(f"kimp value: {kimp_value}")
        else:
            print("Could not find 'kimp' variable in the response")

except requests.exceptions.RequestException as e:
    print(f"An error occurred: {e}")
