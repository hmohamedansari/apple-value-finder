# scraper.py
import requests
from bs4 import BeautifulSoup
import json
import time
import re # Import regular expression module

# --- Configuration ---
# Specific URL for 13-inch MacBook Air M-series (Update if needed)
# We will add more URLs later for other models/sizes
TARGET_URLS = [
    'https://www.apple.com/in/shop/buy-mac/macbook-air/13-inch', # 13-inch Air
    "https://www.apple.com/in/shop/buy-mac/macbook-air/15-inch", # 15-inch Air
    "https://www.apple.com/in/shop/buy-mac/macbook-pro/14-inch-macbook-pro", # 14-inch Pro
    "https://www.apple.com/in/shop/buy-mac/macbook-pro/16-inch-macbook-pro", # 16-inch Pro
    # Add URLs for 15-inch Air, MacBook Pro, iPads etc. here later
    # 'https://www.apple.com/in/shop/buy-ipad/ipad-air',

    # --- Desktop Macs ---
    'https://www.apple.com/in/shop/buy-mac/imac',
    'https://www.apple.com/in/shop/buy-mac/mac-mini',
    'https://www.apple.com/in/shop/buy-mac/mac-studio',
    #'https://www.apple.com/in/shop/buy-mac/mac-pro',

    # --- iPhones (Specific Configurations) ---
    # iPhone 16 Pro
    'https://www.apple.com/in/shop/buy-iphone/iphone-16-pro/6.3%22-display-128gb-black-titanium',
    'https://www.apple.com/in/shop/buy-iphone/iphone-16-pro/6.3%22-display-256gb-black-titanium',
    'https://www.apple.com/in/shop/buy-iphone/iphone-16-pro/6.3%22-display-512gb-black-titanium',
    'https://www.apple.com/in/shop/buy-iphone/iphone-16-pro/6.3%22-display-1tb-black-titanium',
    # iPhone 16 Pro Max
    'https://www.apple.com/in/shop/buy-iphone/iphone-16-pro/6.9%22-display-256gb-black-titanium',
    'https://www.apple.com/in/shop/buy-iphone/iphone-16-pro/6.9%22-display-512gb-black-titanium',
    'https://www.apple.com/in/shop/buy-iphone/iphone-16-pro/6.9%22-display-1tb-black-titanium',
    # iPhone 16
    'https://www.apple.com/in/shop/buy-iphone/iphone-16/6.1%22-display-128gb-black',
    'https://www.apple.com/in/shop/buy-iphone/iphone-16/6.1%22-display-256gb-black',
    'https://www.apple.com/in/shop/buy-iphone/iphone-16/6.1%22-display-512gb-black',
    # iPhone 16 Plus
    'https://www.apple.com/in/shop/buy-iphone/iphone-16/6.7%22-display-128gb-black',
    'https://www.apple.com/in/shop/buy-iphone/iphone-16/6.7%22-display-256gb-black',
    'https://www.apple.com/in/shop/buy-iphone/iphone-16/6.7%22-display-512gb-black',

    # iPhone 15 (Example: Blue - add other colors/models if needed)
    'https://www.apple.com/in/shop/buy-iphone/iphone-15/6.1%22-display-128gb-blue',
    'https://www.apple.com/in/shop/buy-iphone/iphone-15/6.1%22-display-256gb-blue',
    'https://www.apple.com/in/shop/buy-iphone/iphone-15/6.1%22-display-512gb-blue',
    # iPhone 15 Plus (Example: Blue)
    'https://www.apple.com/in/shop/buy-iphone/iphone-15/6.7%22-display-128gb-blue',
    'https://www.apple.com/in/shop/buy-iphone/iphone-15/6.7%22-display-256gb-blue',
    'https://www.apple.com/in/shop/buy-iphone/iphone-15/6.7%22-display-512gb-blue',
]

# Pretend to be a browser
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.88 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9', # Often helpful
}

def extract_specs(spec_string):
    """
    Uses regular expressions to extract specs from a string like:
    '10-Core CPU 8-Core GPU 16GB Unified Memory 256GB SSD Storage'
    Returns a dictionary {'cpu_cores': int, 'gpu_cores': int, 'ram_gb': int, 'storage_gb': int}
    """
    specs = {
        'cpu_cores': 0,
        'gpu_cores': 0,
        'ram_gb': 0,
        'storage_gb': 0
    }
    try:
        # Extract CPU cores
        match = re.search(r'(\d+)-Core CPU', spec_string, re.IGNORECASE)
        if match: specs['cpu_cores'] = int(match.group(1))

        # Extract GPU cores
        match = re.search(r'(\d+)-Core GPU', spec_string, re.IGNORECASE)
        if match: specs['gpu_cores'] = int(match.group(1))

        # Extract RAM
        match = re.search(r'(\d+)GB Unified Memory', spec_string, re.IGNORECASE)
        if match: specs['ram_gb'] = int(match.group(1))

        # Extract Storage (handling GB and TB)
        match_gb = re.search(r'(\d+)GB SSD Storage', spec_string, re.IGNORECASE)
        match_tb = re.search(r'(\d+)TB SSD Storage', spec_string, re.IGNORECASE)
        if match_gb:
            specs['storage_gb'] = int(match_gb.group(1))
        elif match_tb:
            specs['storage_gb'] = int(match_tb.group(1)) * 1024 # Convert TB to GB

    except Exception as e:
        print(f"Error parsing spec string '{spec_string}': {e}")
    return specs

# scraper.py (Replace the parse_product_page function only)

def parse_product_page(url, soup):
    """
    Parses the BeautifulSoup object for a specific Apple product page structure.
    Attempts to handle both MacBook Air and MacBook Pro pages.
    Includes debugging for Pro pages.
    """
    products = []
    is_pro_page = 'macbook-pro' in url # Check if it's likely a Pro page based on URL

    # --- Get Base Product Name (Improved) ---
    base_name = "Unknown Mac" # Default
    title_tag = soup.find('title')
    page_title_text = title_tag.text.lower() if title_tag else ""

    if 'macbook pro' in page_title_text:
        if '14-inch' in page_title_text or '14"' in page_title_text:
            base_name = "14-inch MacBook Pro"
        elif '16-inch' in page_title_text or '16"' in page_title_text:
            base_name = "16-inch MacBook Pro"
        else:
            base_name = "MacBook Pro" # Fallback if size not in title
    elif 'macbook air' in page_title_text:
        if '13-inch' in page_title_text or '13"' in page_title_text :
             base_name = "13-inch MacBook Air"
        elif '15-inch' in page_title_text or '15"' in page_title_text:
             base_name = "15-inch MacBook Air"
        else:
             base_name = "MacBook Air" # Fallback
    # Add more base name detection as needed (iPad, iMac etc.)
    elif 'ipad air' in page_title_text: base_name = "iPad Air"
    elif 'ipad pro' in page_title_text: base_name = "iPad Pro"
    elif 'imac' in page_title_text: base_name = "iMac"
    elif 'mac mini' in page_title_text: base_name = "Mac mini"


    print(f"Determined base name: '{base_name}' for URL: {url}")
    if is_pro_page: print("DEBUG: Processing as MacBook Pro page.")

    # --- CORE SCRAPING LOGIC ---
    # Try the common price selector first
    price_selector = 'span.as-price-currentprice'
    price_elements = soup.find_all('span', class_='as-price-currentprice')

    # Fallback selectors if the first one fails (might be needed for Pro)
    if not price_elements:
        price_selector = 'span.rf-price-label' # Another common one
        print(f"Selector 'span.as-price-currentprice' failed, trying '{price_selector}'...")
        price_elements = soup.find_all('span', class_='rf-price-label')
    if not price_elements:
         price_selector = 'div.currentprice' # Yet another possibility
         print(f"Selector 'span.rf-price-label' failed, trying '{price_selector}'...")
         price_elements = soup.find_all('div', class_='currentprice') # Price might be in a div

    print(f"Found {len(price_elements)} potential price elements using selector '{price_selector}'")
    if is_pro_page and not price_elements:
         print("DEBUG (Pro Page): Failed to find price elements with known selectors.")

    if not price_elements:
        print(f"Warning: Could not find any price elements using known selectors. Scraping for this page might fail.")
        return []

    processed_containers = set()

    for price_element in price_elements:
        try:
            # --- Find Parent Container ---
            # Try common container patterns, maybe add Pro-specific ones if identified later
            container = price_element.find_parent('div', class_=re.compile(r'rf-configuration|rf-product|as-producttile|pdp-options|rf-chip-selection-option|product-selection', re.IGNORECASE))
            if not container: container = price_element.find_parent('form')
            if not container:
                 parent = price_element.parent
                 for _ in range(5): # Go up max 5 levels
                      if parent: parent = parent.parent
                      else: break
                 container = parent

            if not container:
                if is_pro_page: print("DEBUG (Pro Page): Could not find parent container for a price element.")
                continue

            container_text_id = container.get_text(strip=True, separator='|')
            if container_text_id in processed_containers: continue
            processed_containers.add(container_text_id)

            # --- Extract Price ---
            price_text = price_element.get_text(strip=True)
            price_cleaned = price_text.replace('₹', '').replace(',', '').strip()
            if '.' in price_cleaned: price_cleaned = price_cleaned.split('.')[0]
            if price_cleaned.isdigit(): price_inr = int(price_cleaned)
            else:
                 if is_pro_page: print(f"DEBUG (Pro Page): Invalid price '{price_text}'. Skipping.")
                 else: print(f"Warning: Invalid price '{price_text}'. Skipping container.")
                 continue

            # --- Extract Core Specs (CPU/GPU/RAM/Storage) ---
            specs = {'cpu_cores': 0, 'gpu_cores': 0, 'ram_gb': 0, 'storage_gb': 0}
            spec_string = ""
            # Define the spec keyword checker function
            def contains_core_specs(tag):
                # Check common tags where specs might appear
                if not tag.name in ['h3', 'h4', 'p', 'span', 'div', 'li']: return False
                text = tag.get_text().lower()
                # Relaxed check: look for CPU/GPU AND Memory AND SSD keywords
                has_cpu_gpu = 'core cpu' in text or 'core gpu' in text
                has_memory = 'gb unified memory' in text or 'gb memory' in text or 'gb ram' in text
                has_storage = 'gb ssd' in text or 'tb ssd' in text
                return has_cpu_gpu and has_memory and has_storage

            spec_element = container.find(contains_core_specs)

            if spec_element:
                spec_string = spec_element.get_text(separator=' ', strip=True)
                specs = extract_specs(spec_string) # Use the existing robust extraction function
                if specs['ram_gb'] == 0 or specs['storage_gb'] == 0:
                     if is_pro_page: print(f"DEBUG (Pro Page): Found spec element but failed parse RAM/Storage from '{spec_string[:100]}...'.")
                     else: print(f"Warning: Found spec element but failed to parse RAM/Storage from '{spec_string[:100]}...'. Skipping container.")
                     continue
                # else: print(f"Successfully parsed specs from element: {spec_string[:50]}...") # Debug
            else:
                # If direct find fails, try finding all text and searching within it (less reliable)
                all_text = container.get_text(separator=' ', strip=True)
                specs = extract_specs(all_text)
                if specs['ram_gb'] > 0 and specs['storage_gb'] > 0:
                     if is_pro_page: print("DEBUG (Pro Page): Parsed specs from container's full text as fallback.")
                     spec_string = all_text # Use the full text as the source string
                else:
                     if is_pro_page: print(f"DEBUG (Pro Page): Could not find element containing core specs for price {price_inr}. Also failed fallback text search.")
                     else: print(f"Warning: Could not find element containing core specs (CPU/RAM/Storage) for price {price_inr}. Skipping container.")
                     continue # Skip if no core specs found

            # --- Extract Chip Name (Handle M Pro/Max) ---
            chip_name = "Unknown M-Series"
            # Try finding chip name within the container OR use the spec string
            # Look for M followed by digit, possibly followed by Pro/Max/Ultra
            chip_match = re.search(r'(M\d+(\s*(Pro|Max|Ultra))?)', container.get_text(), re.IGNORECASE)
            if chip_match:
                 chip_name = chip_match.group(1).upper().replace(" ", "") # Consolidate like M3PRO
            else:
                 if is_pro_page: print(f"DEBUG (Pro Page): Could not determine M-series chip for price {price_inr} from container text.")
                 else: print(f"Warning: Could not determine M-series chip for price {price_inr}. Skipping.")
                 continue


            # --- Construct Full Product Name ---
            ram_val = specs.get('ram_gb', '?')
            storage_val = specs.get('storage_gb', '?')
            # Use the detected base_name
            full_name = f"{base_name} {chip_name} ({ram_val}GB RAM, {storage_val}GB SSD)"

            # --- Add Product if Valid ---
            if price_inr > 0 and specs['ram_gb'] > 0 and specs['storage_gb'] > 0 and chip_name != "Unknown M-Series":
                product_data = {
                    'name': full_name,
                    'chip': chip_name,
                    'cpu_cores': specs.get('cpu_cores', 0),
                    'gpu_cores': specs.get('gpu_cores', 0),
                    'ram_gb': specs.get('ram_gb', 0),
                    'storage_gb': specs.get('storage_gb', 0),
                    'price_inr': price_inr,
                    'source_url': url
                }
                products.append(product_data)
                # print(f"Successfully added: {product_data}") # Debug
            else:
                 if is_pro_page: print(f"DEBUG (Pro Page): Skipping invalid data: Name={full_name}, Price={price_inr}, Specs={specs}, Chip={chip_name}")
                 else: print(f"Skipping invalid data for container: Name={full_name}, Price={price_inr}, Specs={specs}")

        except Exception as e:
            print(f"Error processing a container related to price element: {e}")
            # import traceback # Uncomment for detailed stack trace
            # traceback.print_exc() # Uncomment for detailed stack trace
            continue

    return products

# Ensure the rest of scraper.py (imports, TARGET_URLS, HEADERS, extract_specs,

# scrape_apple_data, main block) remains the same.

def scrape_apple_data(output_file):
    """Scrapes specified Apple product pages and saves unique data to a JSON file."""
    print("Starting Apple India scrape...")
    all_products = []
    session = requests.Session() # Use a session object
    session.headers.update(HEADERS)

    for url in TARGET_URLS:
        print(f"\nAttempting to scrape: {url}")
        try:
            response = session.get(url, timeout=30) # Increased timeout
            response.raise_for_status() # Raise HTTP errors
            print(f"Successfully fetched {url} (Status: {response.status_code})")

            soup = BeautifulSoup(response.content, 'lxml') # Use lxml parser (install if needed: pip install lxml)
            # If lxml fails, fallback: soup = BeautifulSoup(response.content, 'html.parser')

            page_products = parse_product_page(url, soup)
            print(f"Extracted {len(page_products)} configurations from {url}")
            all_products.extend(page_products)

            # Be polite - wait between requests
            time.sleep(3)

        except requests.exceptions.RequestException as e:
            print(f"Error fetching {url}: {e}")
        except Exception as e:
            print(f"Error processing {url}: {e}") # Catch other errors like parsing

    # --- Data Deduplication ---
    unique_products = []
    seen_identifiers = set()
    for product in all_products:
        # Create a unique identifier based on key specs and price
        identifier = (
            product['chip'],
            product['cpu_cores'],
            product['gpu_cores'],
            product['ram_gb'],
            product['storage_gb'],
            product['price_inr'],
            product['source_url'] # Include URL in case same spec exists for 13" vs 15" etc.
        )
        if identifier not in seen_identifiers:
            unique_products.append(product)
            seen_identifiers.add(identifier)
        else:
            print(f"Duplicate detected and removed: {product['name']}")


    print(f"\nScraping complete. Found {len(unique_products)} unique M-series configurations across all pages.")

    # Get current timestamp
    timestamp = time.time()

    # Prepare data for saving
    data_to_save = {
        "timestamp": timestamp,
        "products": unique_products
    }

    # Save data to JSON file
    try:
        with open(output_file, 'w', encoding='utf-8') as f: # Ensure utf-8 encoding
            json.dump(data_to_save, f, indent=4, ensure_ascii=False) # ensure_ascii=False for non-latin chars if any
        print(f"Data successfully saved to {output_file}")
    except IOError as e:
        print(f"Error saving data to {output_file}: {e}")
    except Exception as e:
        print(f"An unexpected error occurred during file saving: {e}")


# Allow running the scraper directly for testing
if __name__ == '__main__':
    # Install lxml if you haven't: pip install lxml
    scrape_apple_data('apple_products.json')