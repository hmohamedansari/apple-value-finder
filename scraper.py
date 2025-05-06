import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime
from urllib.parse import unquote

# --- Configuration ---
USER_PROVIDED_URLS = [
    'https://www.apple.com/in/shop/buy-mac/macbook-air/13-inch',
    "https://www.apple.com/in/shop/buy-mac/macbook-air/15-inch",
    "https://www.apple.com/in/shop/buy-mac/macbook-pro/14-inch-macbook-pro",
    "https://www.apple.com/in/shop/buy-mac/macbook-pro/16-inch-macbook-pro",
    'https://www.apple.com/in/shop/buy-mac/imac',
    'https://www.apple.com/in/shop/buy-mac/mac-mini',
    'https://www.apple.com/in/shop/buy-mac/mac-studio',
    'https://www.apple.com/in/shop/buy-iphone/iphone-16-pro/6.3%22-display-128gb-black-titanium',
    'https://www.apple.com/in/shop/buy-iphone/iphone-16-pro/6.3%22-display-256gb-black-titanium',
    'https://www.apple.com/in/shop/buy-iphone/iphone-16-pro/6.3%22-display-512gb-black-titanium',
    'https://www.apple.com/in/shop/buy-iphone/iphone-16-pro/6.3%22-display-1tb-black-titanium',
    'https://www.apple.com/in/shop/buy-iphone/iphone-16-pro/6.9%22-display-256gb-black-titanium',
    'https://www.apple.com/in/shop/buy-iphone/iphone-16-pro/6.9%22-display-512gb-black-titanium',
    'https://www.apple.com/in/shop/buy-iphone/iphone-16-pro/6.9%22-display-1tb-black-titanium',
    'https://www.apple.com/in/shop/buy-iphone/iphone-16/6.1%22-display-128gb-black',
    'https://www.apple.com/in/shop/buy-iphone/iphone-16/6.1%22-display-256gb-black',
    'https://www.apple.com/in/shop/buy-iphone/iphone-16/6.1%22-display-512gb-black',
    'https://www.apple.com/in/shop/buy-iphone/iphone-16/6.7%22-display-128gb-black',
    'https://www.apple.com/in/shop/buy-iphone/iphone-16/6.7%22-display-256gb-black',
    'https://www.apple.com/in/shop/buy-iphone/iphone-16/6.7%22-display-512gb-black',
    'https://www.apple.com/in/shop/buy-iphone/iphone-15/6.1%22-display-128gb-blue',
    'https://www.apple.com/in/shop/buy-iphone/iphone-15/6.1%22-display-256gb-blue',
    'https://www.apple.com/in/shop/buy-iphone/iphone-15/6.1%22-display-512gb-blue',
    'https://www.apple.com/in/shop/buy-iphone/iphone-15/6.7%22-display-128gb-blue',
    'https://www.apple.com/in/shop/buy-iphone/iphone-15/6.7%22-display-256gb-blue',
    'https://www.apple.com/in/shop/buy-iphone/iphone-15/6.7%22-display-512gb-blue',
]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
}
OUTPUT_FILE = 'apple_products.json'

def get_product_details_from_url(url):
    path_parts = [part for part in url.split('/') if part]
    category = "Unknown"
    name = "Unknown Product"

    if 'buy-mac' in path_parts:
        product_type_index = path_parts.index('buy-mac') + 1
        product_type = path_parts[product_type_index] if len(path_parts) > product_type_index else "Mac"

        if product_type == 'macbook-air': category = "MacBook Air"
        elif product_type == 'macbook-pro': category = "MacBook Pro"
        elif product_type == 'imac': category = "iMac"
        elif product_type == 'mac-mini': category = "Mac mini"
        elif product_type == 'mac-studio': category = "Mac Studio"
        else: category = "Mac"
        name_parts = [unquote(p.replace('-', ' ').title()) for p in path_parts[product_type_index:] if '%' not in p and 'display' not in p and 'gb' not in p and 'tb' not in p]
        name = ' '.join(name_parts) if name_parts else category


    elif 'buy-iphone' in path_parts:
        category = "iPhone"
        try:
            model_index = path_parts.index('buy-iphone') + 1
            model_and_specs = path_parts[model_index:]
            name = unquote(' '.join(model_and_specs)).replace('-', ' ').replace('/', ' ')
            name = re.sub(r'(iphone\s?\d+\s?(?:pro|max|plus|se)?)', lambda m: m.group(1).upper(), name, flags=re.I)
            name = re.sub(r'(\d+\.?\d*)"', r'\1-inch', name)
            name = re.sub(r'(\d+)(gb|tb)', lambda m: m.group(1) + m.group(2).upper(), name, flags=re.I)
            name = ' '.join(word.capitalize() if not any(char.isdigit() for char in word) and word not in ["GB", "TB"] else word for word in name.split())
        except ValueError:
            name = "iPhone (Unknown Configuration)"
    return {"name": name.strip(), "category": category, "url": url}

PROCESSED_URLS = [get_product_details_from_url(url) for url in USER_PROVIDED_URLS]

def get_soup(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=20)
        response.raise_for_status()
        return BeautifulSoup(response.content, 'lxml')
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

def extract_price_from_text(text):
    if not text: return None
    match = re.search(r'₹\s*([\d,]+(?:\.\d{2})?)', text)
    if match:
        price_str = match.group(1).replace(',', '')
        try: return float(price_str)
        except ValueError: return None
    return None

def parse_mac_specs(spec_string, product_base_name=""):
    specs = {"chip": "N/A", "cpu_cores": 0, "gpu_cores": 0, "ram_gb": 0, "storage_tb": 0, "screen_size_inch": 0}
    if not spec_string: spec_string = ""
    chip_match = re.search(r'(Apple\sM\d\s?(?:Pro|Max|Ultra|Extreme)?\s?chip)', spec_string, re.IGNORECASE)
    if chip_match: specs["chip"] = chip_match.group(1).strip()
    else:
        chip_match_simple = re.search(r'(M\d\s?(?:Pro|Max|Ultra|Extreme)?)', spec_string, re.IGNORECASE)
        if chip_match_simple: specs["chip"] = f"Apple {chip_match_simple.group(1).strip()} chip"
    cpu_match = re.search(r'(\d+)-core\sCPU', spec_string, re.IGNORECASE)
    if cpu_match: specs["cpu_cores"] = int(cpu_match.group(1))
    gpu_match = re.search(r'(\d+)-core\sGPU', spec_string, re.IGNORECASE)
    if gpu_match: specs["gpu_cores"] = int(gpu_match.group(1))
    ram_match = re.search(r'(\d+)GB\s(?:unified\s)?memory', spec_string, re.IGNORECASE)
    if not ram_match: ram_match = re.search(r'(\d+)GB\sRAM', spec_string, re.IGNORECASE)
    if ram_match: specs["ram_gb"] = int(ram_match.group(1).replace('GB', ''))
    storage_match_gb = re.search(r'(\d+)GB\sSSD', spec_string, re.IGNORECASE)
    storage_match_tb = re.search(r'(\d+)TB\sSSD', spec_string, re.IGNORECASE)
    if storage_match_tb: specs["storage_tb"] = int(storage_match_tb.group(1))
    elif storage_match_gb: specs["storage_tb"] = int(storage_match_gb.group(1)) / 1000
    screen_size_text = product_base_name + " " + spec_string
    screen_match = re.search(r'(\d{2})-inch', screen_size_text, re.IGNORECASE)
    if screen_match: specs["screen_size_inch"] = int(screen_match.group(1))
    else:
        for size in ["13", "14", "15", "16", "24", "27"]:
            if f"{size} inch" in screen_size_text.lower() or f"{size}-inch" in product_base_name.lower():
                specs["screen_size_inch"] = int(size)
                break
    return specs

def parse_iphone_specs_from_name(name_from_url):
    specs = {"chip": "N/A", "storage_tb": 0, "screen_size_inch": 0.0, "cpu_cores": 0, "gpu_cores": 0, "ram_gb": 0}
    screen_match = re.search(r'(\d+\.?\d*)\s*(?:inch|")', name_from_url, re.IGNORECASE)
    if screen_match: specs["screen_size_inch"] = float(screen_match.group(1))
    storage_match_gb = re.search(r'(\d+)GB', name_from_url, re.IGNORECASE)
    storage_match_tb = re.search(r'(\d+)TB', name_from_url, re.IGNORECASE)
    if storage_match_tb: specs["storage_tb"] = int(storage_match_tb.group(1))
    elif storage_match_gb: specs["storage_tb"] = int(storage_match_gb.group(1)) / 1000
    if "iPhone SE" in name_from_url: specs["chip"] = "A-series Bionic (SE)"
    elif "Pro" in name_from_url or "Max" in name_from_url: specs["chip"] = "A-series Bionic Pro/Max (latest)"
    elif re.search(r'iPhone\s\d+', name_from_url): specs["chip"] = "A-series Bionic (latest)"
    return specs

def scrape_mac_page(product_base_name, url, category):
    print(f"Scraping Mac page: {product_base_name} from {url}")
    soup = get_soup(url)
    if not soup: return []
    products = []
    product_containers = soup.select('div.rc-productbundle-item, div.as-producttile, div.rf-producttile, .rf-bundle-selection-item')
    if not product_containers:
        print(f"  No Mac product containers found on {url} using primary selectors. Trying broader search or page might be dynamic / single item.")
        page_title = soup.select_one('head > title')
        page_title_text = page_title.get_text(strip=True) if page_title else product_base_name
        price_element = soup.select_one('.rc-prices-fullprice, .currentprice .price-value, .as-price-currentprice .price-value, span[data-autom="price"]')
        price_text = price_element.get_text(strip=True) if price_element else None
        if not price_text:
            price_match_page = soup.find(string=re.compile(r'₹\s*([\d,]+(?:\.\d{2})?)'))
            if price_match_page: price_text = price_match_page.strip()
        price = extract_price_from_text(price_text)
        if price:
            print(f"  Found a single price on Mac page: {price}. Assuming it's for {page_title_text}")
            specs = parse_mac_specs(soup.get_text(), page_title_text)
            product_data = {"name": page_title_text, "category": category, "base_model_name": product_base_name, "price_inr": price, **specs, "url": url, "scraped_at": datetime.now().isoformat()}
            products.append(product_data)
            print(f"    Successfully scraped single Mac: {product_data['name']} - Price: {product_data['price_inr']}")
        else:
            print(f"  No product containers or single price found for Mac: {product_base_name} on {url}")
        return products
    print(f"  Found {len(product_containers)} potential Mac product containers on {url}.")
    for i, item_container in enumerate(product_containers):
        try:
            title_element = item_container.select_one('.rc-productbundle-title, .as-producttile-title, .rf-producttile-title, .rf-bundle-header-title')
            full_description = title_element.get_text(separator=' ', strip=True) if title_element else product_base_name
            price_element = item_container.select_one('.rc-productbundle-price .price-value, .as-producttile-pricecurrent .price-value, .rf-producttile-pricecurrent .price-value, .rf-bundle-price .price-value')
            price_text = price_element.get_text(strip=True) if price_element else None
            if not price_text:
                price_match_in_item = item_container.find(string=re.compile(r'₹\s*([\d,]+(?:\.\d{2})?)'))
                if price_match_in_item: price_text = price_match_in_item.strip()
            price = extract_price_from_text(price_text)
            if not price: continue
            specs_text_element = item_container.select_one('.rc-productbundle-configsummary, .as-producttile-specs, .rf-producttile-specs, .rf-bundle-summary')
            specs_text_content = specs_text_element.get_text(separator=' ', strip=True) if specs_text_element else full_description
            specs = parse_mac_specs(specs_text_content, full_description)
            product_name = full_description
            if "Apple" not in product_name and "Mac" in category: product_name = f"{product_base_name} - {full_description}"
            if (specs["cpu_cores"] == 0 or specs["gpu_cores"] == 0) and "Mac" in category and specs["chip"] != "N/A":
                 print(f"    Warning for {product_name}: Missing CPU/GPU cores. CPU: {specs['cpu_cores']}, GPU: {specs['gpu_cores']}. From: '{specs_text_content[:100]}...'")
            product_data = {"name": product_name.strip(), "category": category, "base_model_name": product_base_name, "price_inr": price, **specs, "url": url, "scraped_at": datetime.now().isoformat()}
            products.append(product_data)
            print(f"    Successfully scraped Mac config: {product_name.strip()} - Price: {price} - CPU: {specs['cpu_cores']}, GPU: {specs['gpu_cores']}, RAM: {specs['ram_gb']}GB, Storage: {specs['storage_tb']}TB")
        except Exception as e:
            print(f"    Error processing a Mac item from {url} (Item {i+1}): {e}")
    return products

def scrape_iphone_page(product_name_from_url, url, category):
    print(f"Scraping iPhone (specific config): {product_name_from_url} from {url}")
    soup = get_soup(url)
    if not soup: return []
    products = []
    price_text = None
    price_selectors = ['div[data-autom="price"] span.price-value', 'span[data-autom="price"]', '.rc-prices-fullprice .price-value', '.as-price-currentprice .price-value', '.rf-pdp-price .price-value', '.hero-price .price-value', 'span.currentprice']
    for selector in price_selectors:
        price_element = soup.select_one(selector)
        if price_element:
            price_text = price_element.get_text(strip=True)
            break
    if not price_text:
        price_match_page = soup.find(string=re.compile(r'₹\s*([\d,]+(?:\.\d{2})?)'))
        if price_match_page: price_text = price_match_page.strip()
    price = extract_price_from_text(price_text)
    if price:
        specs = parse_iphone_specs_from_name(product_name_from_url)
        base_model_name_match = re.match(r'(IPHONE\s\d+\s?(?:PRO|MAX|PLUS|SE)?)', product_name_from_url, re.I)
        base_model_name = base_model_name_match.group(1) if base_model_name_match else "iPhone"

        product_data = {
            "name": product_name_from_url, "category": category, "base_model_name": base_model_name,
            "price_inr": price, **specs, "url": url, "scraped_at": datetime.now().isoformat()
        }
        products.append(product_data)
        print(f"  Successfully scraped iPhone: {product_name_from_url} - Price: {price}, Storage: {specs['storage_tb']}TB, Screen: {specs['screen_size_inch']}\"")
    else:
        print(f"  Could not find price for iPhone: {product_name_from_url} on {url}. Price text found: '{price_text}'")
    return products

def run_scraper_and_get_data(): # Renamed main to this
    all_products = []
    for item_details in PROCESSED_URLS:
        name = item_details["name"]
        url = item_details["url"]
        category_type = item_details["category"]
        print(f"\n--- Scraping: {name} ({category_type}) ---")
        print(f"URL: {url}")
        scraped_data = []
        if "Mac" in category_type:
            scraped_data = scrape_mac_page(name, url, category_type)
        elif "iPhone" in category_type:
            scraped_data = scrape_iphone_page(name, url, category_type)
        else:
            print(f"Warning: No specific scraper defined for category type '{category_type}'. Skipping {name}.")
        if scraped_data:
            all_products.extend(scraped_data)
        else:
            print(f"  No data scraped for {name} from {url}.")
    if all_products:
        all_products.sort(key=lambda x: (x['category'], x.get('price_inr', float('inf'))))
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(all_products, f, indent=4, ensure_ascii=False)
        print(f"\nSuccessfully scraped {len(all_products)} products and saved to {OUTPUT_FILE}")
    else:
        print("\nNo products were scraped. The output file was not updated.")
    return all_products # Return the data

if __name__ == "__main__":
    run_scraper_and_get_data() # Call the renamed function if script is run directly