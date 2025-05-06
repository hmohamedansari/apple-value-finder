# scraper.py
import requests
from bs4 import BeautifulSoup
import json
import time
import random
import re
import urllib.parse # For decoding URL components

# --- Configuration ---
OUTPUT_FILE = "apple_products.json"
USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.88 Safari/537.36'
REQUEST_TIMEOUT = 25
SLEEP_MIN = 2.5
SLEEP_MAX = 5.5

# List of Apple Store pages/configurations to scrape (India)
TARGET_URLS = [
    # --- MacBooks ---
    # 'https://www.apple.com/in/shop/buy-mac/macbook-air/13-inch',
    # "https://www.apple.com/in/shop/buy-mac/macbook-air/15-inch",
    # "https://www.apple.com/in/shop/buy-mac/macbook-pro/14-inch-macbook-pro",
    # "https://www.apple.com/in/shop/buy-mac/macbook-pro/16-inch-macbook-pro",

    # --- Desktop Macs ---
    'https://www.apple.com/in/shop/buy-mac/imac',
    'https://www.apple.com/in/shop/buy-mac/mac-mini',
    'https://www.apple.com/in/shop/buy-mac/mac-studio',

    # --- iPhones (Specific Configurations) ---
    # # iPhone 16 Pro
    # 'https://www.apple.com/in/shop/buy-iphone/iphone-16-pro/6.3%22-display-128gb-black-titanium',
    # 'https://www.apple.com/in/shop/buy-iphone/iphone-16-pro/6.3%22-display-256gb-black-titanium',
    # 'https://www.apple.com/in/shop/buy-iphone/iphone-16-pro/6.3%22-display-512gb-black-titanium',
    # 'https://www.apple.com/in/shop/buy-iphone/iphone-16-pro/6.3%22-display-1tb-black-titanium',
    # # iPhone 16 Pro Max
    # 'https://www.apple.com/in/shop/buy-iphone/iphone-16-pro/6.9%22-display-256gb-black-titanium',
    # 'https://www.apple.com/in/shop/buy-iphone/iphone-16-pro/6.9%22-display-512gb-black-titanium',
    # 'https://www.apple.com/in/shop/buy-iphone/iphone-16-pro/6.9%22-display-1tb-black-titanium',
    # # iPhone 16
    # 'https://www.apple.com/in/shop/buy-iphone/iphone-16/6.1%22-display-128gb-black',
    # 'https://www.apple.com/in/shop/buy-iphone/iphone-16/6.1%22-display-256gb-black',
    # 'https://www.apple.com/in/shop/buy-iphone/iphone-16/6.1%22-display-512gb-black',
    # # iPhone 16 Plus
    # 'https://www.apple.com/in/shop/buy-iphone/iphone-16/6.7%22-display-128gb-black',
    # 'https://www.apple.com/in/shop/buy-iphone/iphone-16/6.7%22-display-256gb-black',
    # 'https://www.apple.com/in/shop/buy-iphone/iphone-16/6.7%22-display-512gb-black',

    # # iPhone 15 (Example: Blue - add other colors/models if needed)
    # 'https://www.apple.com/in/shop/buy-iphone/iphone-15/6.1%22-display-128gb-blue',
    # 'https://www.apple.com/in/shop/buy-iphone/iphone-15/6.1%22-display-256gb-blue',
    # 'https://www.apple.com/in/shop/buy-iphone/iphone-15/6.1%22-display-512gb-blue',
    # # iPhone 15 Plus (Example: Blue)
    # 'https://www.apple.com/in/shop/buy-iphone/iphone-15/6.7%22-display-128gb-blue',
    # 'https://www.apple.com/in/shop/buy-iphone/iphone-15/6.7%22-display-256gb-blue',
    # 'https://www.apple.com/in/shop/buy-iphone/iphone-15/6.7%22-display-512gb-blue',

    # Add iPhone SE / 14 / 13 specific config URLs if available and needed
]
# Clean up URLs
TARGET_URLS = sorted(list(set(TARGET_URLS)))

# --- Helper Functions ---

def extract_specs(spec_string):
    """Extracts CPU, GPU, RAM, Storage from Mac/Desktop spec strings."""
    specs = {
        'cpu_cores': 0,
        'gpu_cores': 0,
        'ram_gb': 0,
        'storage_gb': 0
    }
    try:
        # Use slightly more flexible regex patterns
        # Extract CPU cores
        match = re.search(r'(\d+)[-\s]Core CPU', spec_string, re.IGNORECASE)
        if match: specs['cpu_cores'] = int(match.group(1))

        # Extract GPU cores
        match = re.search(r'(\d+)[-\s]Core GPU', spec_string, re.IGNORECASE)
        if match: specs['gpu_cores'] = int(match.group(1))

        # Extract RAM (Unified Memory or just Memory/RAM)
        match = re.search(r'(\d+)\s*GB\s*(Unified\s)?Memory', spec_string, re.IGNORECASE)
        if not match: match = re.search(r'(\d+)\s*GB\s*RAM', spec_string, re.IGNORECASE)
        if match: specs['ram_gb'] = int(match.group(1))

        # Extract Storage (handling GB and TB, SSD or Storage)
        match_gb = re.search(r'(\d+)\s*GB\s*(SSD|Storage)', spec_string, re.IGNORECASE)
        match_tb = re.search(r'(\d+)\s*TB\s*(SSD|Storage)', spec_string, re.IGNORECASE)
        if match_gb:
            specs['storage_gb'] = int(match_gb.group(1))
        elif match_tb:
            specs['storage_gb'] = int(match_tb.group(1)) * 1024 # Convert TB to GB

    except Exception as e:
        print(f"Error parsing spec string '{spec_string[:100]}...': {e}")
    return specs

def parse_iphone_from_url(url, soup):
    """
    Parses iPhone data directly from a specific configuration URL.
    Extracts model, size, storage from URL path and price from page content.
    """
    try:
        print(f"-> Parsing as iPhone Config URL: {url}")
        path_segments = [urllib.parse.unquote(seg) for seg in url.split('/') if seg]

        model_segment = path_segments[-2]
        config_segment = path_segments[-1]

        size_match = re.search(r'(\d+(\.\d+)?)"', config_segment)
        display_size = size_match.group(1) if size_match else None

        storage_match = re.search(r'(\d+)(gb|tb)', config_segment, re.IGNORECASE)
        storage_gb = 0
        if storage_match:
            val = int(storage_match.group(1))
            unit = storage_match.group(2).lower()
            storage_gb = val * 1024 if unit == 'tb' else val
        else:
             print(f"-> WARNING: Could not extract storage from config segment: '{config_segment}' in URL: {url}")

        base_name = model_segment.replace('-', ' ').title().replace("Iphone", "iPhone")
        if display_size:
             if 'pro' not in base_name.lower() and display_size in ['6.7', '6.9']:
                 base_name += " Plus"
             elif 'pro' in base_name.lower() and display_size in ['6.7', '6.9']:
                 base_name += " Max"

        full_name = f"{base_name} ({storage_gb}GB)" if storage_gb else base_name

        # --- Extract Price from Page (Revised Logic) ---
        price_inr = 0
        # Regex to find the price pattern (₹ followed by digits/commas, ending with .00)
        price_pattern = re.compile(r'₹\s*([\d,]+)\.00')

        # Search within common tags that might contain the main price
        potential_price_tags = soup.find_all(['span', 'div'], limit=20) # Limit search scope
        found_price_text = None

        for tag in potential_price_tags:
            # Check direct text content first
            price_match = price_pattern.search(tag.get_text(strip=True))
            if price_match and 'mo.' not in tag.get_text(): # Avoid monthly EMI price
                found_price_text = price_match.group(0) # Get the full matched price string e.g., ₹69,900.00
                print(f"-> DEBUG (iPhone Price): Found potential price '{found_price_text}' in tag: {tag.name}.{tag.get('class', '')}")
                break # Assume first prominent match is the one

            # Check within attributes if direct text fails (less likely but possible)
            # for attr_val in tag.attrs.values():
            #     if isinstance(attr_val, str):
            #         price_match = price_pattern.search(attr_val)
            #         if price_match:
            #             found_price_text = price_match.group(0)
            #             print(f"-> DEBUG (iPhone Price): Found potential price '{found_price_text}' in attribute")
            #             break
            # if found_price_text: break


        if found_price_text:
            price_cleaned = re.sub(r'[₹,]', '', found_price_text.split('.')[0]).strip()
            if price_cleaned.isdigit():
                price_inr = int(price_cleaned)
            else:
                 print(f"-> ERROR: Could not convert cleaned price '{price_cleaned}' to int for iPhone URL: {url}")
        else:
            print(f"-> ERROR: Price pattern not found in relevant tags for iPhone URL: {url}")
            return None # Critical failure if price not found

        if price_inr <= 0:
             print(f"-> ERROR: Extracted zero or invalid price ({price_inr}) for iPhone URL: {url}")
             return None

        # --- Construct Product Data ---
        product_data = {
            'name': full_name,
            'base_name': base_name,
            'type': 'iPhone',
            'chip': 'A-Series', # Placeholder - Chip info not easily available on these pages
            'cpu_cores': 0,
            'gpu_cores': 0,
            'ram_gb': 0, # Placeholder - RAM info not easily available
            'storage_gb': storage_gb,
            'price_inr': price_inr,
            'source_url': url
        }
        print(f"-> Success (iPhone URL): {full_name} | Price: {price_inr}")
        return product_data

    except Exception as e:
        print(f"!!! Error parsing iPhone URL {url}: {e} !!!")
        import traceback
        traceback.print_exc() # Print full traceback for iPhone errors
        return None

def parse_product_page(url, soup):
    """
    Parses the BeautifulSoup object. Dispatches to specific parsers based on URL pattern.
    Handles specific iPhone config URLs or generic Mac/Desktop pages.
    """
    # --- Check if it's a specific iPhone configuration URL ---
    if "/shop/buy-iphone/iphone-" in url and len(url.split('/')) > 5:
        iphone_data = parse_iphone_from_url(url, soup)
        return [iphone_data] if iphone_data else []

    # --- Otherwise, handle as Mac/Desktop page ---
    print(f"-> Parsing as Mac/Desktop Page: {url}")
    products = []
    page_type = "Unknown" # Will be determined below

    # --- Get Base Product Name (Mac/Desktop Logic) ---
    base_name = "Unknown Product"
    title_tag = soup.find('title')
    page_title_text = title_tag.text.lower() if title_tag else ""
    url_lower = url.lower()

    # Determine Mac/Desktop base name
    if 'imac' in url_lower or 'imac' in page_title_text: base_name = "iMac"; page_type = "Desktop"
    elif 'mac-mini' in url_lower or 'mac mini' in page_title_text: base_name = "Mac mini"; page_type = "Desktop"
    elif 'mac-studio' in url_lower or 'mac studio' in page_title_text: base_name = "Mac Studio"; page_type = "Desktop"
    elif 'mac-pro' in url_lower or 'mac pro' in page_title_text: base_name = "Mac Pro"; page_type = "Desktop"
    elif 'macbook-pro' in url_lower or 'macbook pro' in page_title_text:
        page_type = "MacBook"
        if '14-inch' in url_lower or '14"' in page_title_text or '14-inch' in page_title_text: base_name = "14-inch MacBook Pro"
        elif '16-inch' in url_lower or '16"' in page_title_text or '16-inch' in page_title_text: base_name = "16-inch MacBook Pro"
        else: base_name = "MacBook Pro"
    elif 'macbook-air' in url_lower or 'macbook air' in page_title_text:
        page_type = "MacBook"
        if '13-inch' in url_lower or '13"' in page_title_text or '13-inch' in page_title_text: base_name = "13-inch MacBook Air"
        elif '15-inch' in url_lower or '15"' in page_title_text or '15-inch' in page_title_text: base_name = "15-inch MacBook Air"
        else: base_name = "MacBook Air"
    else:
        print(f"-> Warning: Could not determine Mac/Desktop base name for URL: {url}")
        if '/buy-mac/' in url_lower: page_type = "Mac" # Generic Mac type

    print(f"-> Determined Base Name: '{base_name}', Page Type: '{page_type}'")

    # --- CORE SCRAPING LOGIC (Mac/Desktop) ---
    price_selectors = [
        'span.as-price-currentprice',
        'span.rf-price-label',
        'div.currentprice'
    ]
    price_elements = []
    used_price_selector = "None"
    for selector in price_selectors:
        elements = soup.select(selector)
        if elements:
            price_elements.extend(elements)
            used_price_selector = selector
            print(f"-> Found {len(elements)} potential price elements using selector '{used_price_selector}'")
            # Use the first successful selector
            if len(elements) > 0: break

    if not price_elements:
        print(f"-> Warning: Could not find any price elements using known selectors for Mac/Desktop page.")
        return []

    processed_containers = set() # Use text hash of container to avoid processing duplicates
    print(f"--- Processing {len(price_elements)} potential price elements ---") # DEBUG

    for i, price_element in enumerate(price_elements):
        print(f"\n--- DEBUG: Processing Price Element #{i+1} ---") # DEBUG
        container = None
        price_inr = 0
        specs = {}
        chip_name = "N/A"
        is_valid = False
        full_name = base_name # Start with base name

        try:
            # --- Extract Price ---
            price_text = price_element.get_text(strip=True)
            print(f"-> DEBUG: Raw Price Text: '{price_text}'") # DEBUG
            price_match = re.search(r'₹\s*([\d,]+)', price_text)
            if not price_match:
                print("-> DEBUG: Price pattern not matched. Skipping element.") # DEBUG
                continue
            price_cleaned = re.sub(r',', '', price_match.group(1)).strip()
            price_inr = int(price_cleaned) if price_cleaned.isdigit() else 0
            print(f"-> DEBUG: Extracted Price (INR): {price_inr}") # DEBUG
            if price_inr <= 0:
                print("-> DEBUG: Price is zero or invalid. Skipping element.") # DEBUG
                continue

            # --- Find Parent Container ---
            container = price_element.find_parent(['div', 'form', 'li'], class_=re.compile(r'config|product|option|selection|tile|item|group|rf-pdp-option', re.IGNORECASE))
            if not container:
                 parent = price_element.parent
                 for level in range(6): # Go up max 6 levels
                      if parent and hasattr(parent, 'find_parent'): parent = parent.parent
                      else: break
                 container = parent

            if not container:
                print("-> DEBUG: Could not find parent container. Skipping element.") # DEBUG
                continue
            else:
                 # Limit container text for hashing and debugging
                 container_text_preview = container.get_text(strip=True, separator='|')[:300]
                 print(f"-> DEBUG: Found Container (Preview): '{container_text_preview}...'.") # DEBUG

            # Use text content hash for deduplication
            container_text_id = container.get_text(strip=True, separator='|')[:250]
            if container_text_id in processed_containers:
                print(f"-> DEBUG: Skipping already processed container (based on text hash).") # DEBUG
                continue
            processed_containers.add(container_text_id)

            # --- Extract Specs (using helper on container text) ---
            container_text_for_specs = container.get_text(separator=' ', strip=True)
            # print(f"-> DEBUG: Container Text for Specs: '{container_text_for_specs[:500]}...'") # DEBUG (Optional - can be very long)
            specs = extract_specs(container_text_for_specs)
            print(f"-> DEBUG: Extracted Specs: {specs}") # DEBUG

            # --- Extract Chip Name ---
            chip_match = re.search(r'(M\d+(\s*(Pro|Max|Ultra))?)', container_text_for_specs, re.IGNORECASE)
            if chip_match:
                 chip_name = chip_match.group(1).upper().replace(" ", "")
            else:
                 if page_type in ["MacBook", "Desktop", "Mac"]: chip_name = "M-Series (Unknown)"
            print(f"-> DEBUG: Extracted Chip: {chip_name}") # DEBUG

            # --- Construct Full Product Name ---
            if chip_name != "N/A" and chip_name != "M-Series (Unknown)": full_name += f" {chip_name}"
            ram_val = specs.get('ram_gb', 0)
            storage_val = specs.get('storage_gb', 0)
            spec_parts = []
            if ram_val > 0: spec_parts.append(f"{ram_val}GB RAM")
            if storage_val > 0: spec_parts.append(f"{storage_val}GB SSD")
            if spec_parts: full_name += f" ({', '.join(spec_parts)})"
            print(f"-> DEBUG: Constructed Full Name: {full_name}") # DEBUG

            # --- Validation ---
            is_valid = price_inr > 0 and page_type != "Unknown"
            if page_type in ["MacBook", "Desktop", "Mac"]:
                # For Macs, require storage and a chip name (even if unknown M-series)
                is_valid = is_valid and specs['storage_gb'] > 0 and chip_name != "N/A"
            print(f"-> DEBUG: Validation Check Result: {is_valid}") # DEBUG

            if is_valid:
                product_data = {
                    'name': full_name,
                    'base_name': base_name,
                    'type': page_type,
                    'chip': chip_name,
                    'cpu_cores': specs.get('cpu_cores', 0),
                    'gpu_cores': specs.get('gpu_cores', 0),
                    'ram_gb': specs.get('ram_gb', 0),
                    'storage_gb': specs.get('storage_gb', 0),
                    'price_inr': price_inr,
                    'source_url': url
                }
                # Avoid adding exact duplicates based on key fields from the *same page*
                identifier = (product_data['name'], product_data['price_inr'])
                if identifier not in [(p['name'], p['price_inr']) for p in products]:
                    products.append(product_data)
                    print(f"-> Success (Mac/Desktop): Added product - {full_name} | Price: {price_inr}") # DEBUG Success
                # else: # Debugging duplicates on same page
                    # print(f"-> DEBUG: Skipping duplicate product on same page: {identifier}")

        except Exception as e:
            print(f"!!! Error processing a Mac/Desktop container/element #{i+1}: {e} !!!")
            import traceback
            traceback.print_exc() # Print full traceback for Mac errors
            continue # Move to the next price element

    print(f"--- Finished processing price elements for {url} ---") # DEBUG
    return products


# --- Main Scraping Function ---

def scrape_apple_data(output_file=OUTPUT_FILE):
    """Scrapes all URLs in TARGET_URLS and saves unique products to JSON."""
    all_products = []
    processed_urls = set()
    session = requests.Session()
    session.headers.update({'User-Agent': USER_AGENT})

    for url in TARGET_URLS:
        if url in processed_urls:
            continue
        processed_urls.add(url)

        print(f"\nScraping: {url}")
        try:
            response = session.get(url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status() # Raise HTTPError for bad responses

            # Use lxml if installed, otherwise html.parser
            try:
                soup = BeautifulSoup(response.content, 'lxml')
                parser_used = "lxml"
            except ImportError:
                print("-> lxml not found, using html.parser instead.")
                soup = BeautifulSoup(response.content, 'html.parser')
                parser_used = "html.parser"
            print(f"-> Fetched and parsed with {parser_used}.")

            # parse_product_page returns a list (empty, single iPhone, or multiple Macs)
            products_from_page = parse_product_page(url, soup)

            if products_from_page:
                 print(f"-> Extracted {len(products_from_page)} config(s) from this page.")
                 all_products.extend(products_from_page) # Add all found products
            else:
                 print(f"-> No valid products extracted from: {url}")

            # Respectful delay
            print(f"-> Sleeping for {SLEEP_MIN:.1f}-{SLEEP_MAX:.1f} seconds...")
            time.sleep(random.uniform(SLEEP_MIN, SLEEP_MAX))

        except requests.exceptions.Timeout:
             print(f"!!! Timeout occurred for {url} after {REQUEST_TIMEOUT} seconds !!!")
        except requests.exceptions.RequestException as e:
            print(f"!!! Request failed for {url}: {e} !!!")
        except Exception as e:
            print(f"!!! Error processing {url}: {e} !!!")
            import traceback
            traceback.print_exc()

    # --- Deduplication (Across all scraped pages) ---
    unique_products = []
    seen_products = set()
    print("\n--- Deduplicating results ---")
    for product in all_products:
        # Use a tuple of key attributes to identify uniqueness
        identifier = (
            product.get('name'),
            product.get('price_inr'),
            product.get('storage_gb'), # Key differentiator
            product.get('ram_gb'),     # Also important for Macs
            product.get('type')
        )
        if identifier not in seen_products:
            unique_products.append(product)
            seen_products.add(identifier)
        else: # Debugging duplicates
            print(f"-> Duplicate detected and skipped: {identifier}")


    print(f"\nTotal unique product configurations found across all pages: {len(unique_products)}")

    # --- Save to JSON ---
    timestamp = time.time()
    data_to_save = {
        "timestamp": timestamp,
        "products": unique_products
    }
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data_to_save, f, indent=4, ensure_ascii=False)
        print(f"Data successfully saved to {output_file}")
    except IOError as e:
        print(f"!!! Error saving data to {output_file}: {e} !!!")
    except Exception as e:
        print(f"!!! An unexpected error occurred during file saving: {e} !!!")


    return unique_products

# --- Main Execution Block ---
if __name__ == '__main__':
    print("Starting Apple Product Scraper...")
    # Install lxml if you haven't: pip install lxml
    scraped_products = scrape_apple_data()
    print(f"\nScraping finished. Found {len(scraped_products)} unique products.")