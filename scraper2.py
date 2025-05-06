import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import time

def scrape_macbook_air():
    url = "https://www.apple.com/in/shop/buy-mac/macbook-air"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
    }

    try:
        # Add a delay before making the request
        time.sleep(2)

        response = requests.get(url, headers=headers)
        response.raise_for_status()

        # First, let's print the structure to inspect it
        soup = BeautifulSoup(response.text, 'html.parser')

        # Print the first few lines of HTML to inspect the structure
        print("HTML Structure (first 1000 characters):")
        print(soup.prettify()[:1000])

        # Let's also try to find some key elements
        print("\nTrying to find key elements:")

        # Try different potential selectors
        print("\nAll div elements with 'specifications' in class:")
        specs_divs = soup.find_all('div', class_=lambda x: x and 'specifications' in x)
        print(len(specs_divs))

        print("\nAll price elements:")
        price_elements = soup.find_all(class_=lambda x: x and 'price' in x.lower())
        print(len(price_elements))

        # Print the actual content we find
        print("\nFound content examples:")
        for element in soup.find_all(['div', 'span', 'p'])[:10]:
            if element.text.strip():
                print(f"Tag: {element.name}, Class: {element.get('class', 'No class')}")
                print(f"Content: {element.text.strip()[:100]}\n")

    except requests.RequestException as e:
        print(f"Error fetching the webpage: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

# Run the inspection
scrape_macbook_air()