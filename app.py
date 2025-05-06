from flask import Flask, render_template, request, jsonify
import json
import os
from datetime import datetime, timedelta

# Import the new function from scraper.py
from scraper import run_scraper_and_get_data

app = Flask(__name__)

PRODUCTS_FILE = 'apple_products.json'
LAST_SCRAPED_FILE = 'last_scraped.txt'
SCRAPE_INTERVAL_HOURS = 24 # Scrape data if older than 24 hours

def get_last_scraped_time():
    if os.path.exists(LAST_SCRAPED_FILE):
        with open(LAST_SCRAPED_FILE, 'r') as f:
            return datetime.fromisoformat(f.read().strip())
    return None

def set_last_scraped_time():
    with open(LAST_SCRAPED_FILE, 'w') as f:
        f.write(datetime.now().isoformat())

def load_products():
    last_scraped = get_last_scraped_time()
    needs_scrape = True

    if last_scraped:
        if datetime.now() - last_scraped < timedelta(hours=SCRAPE_INTERVAL_HOURS):
            needs_scrape = False
            print("Scraped data is recent. Loading from file.")
        else:
            print("Scraped data is older than 24 hours. Will re-scrape.")
    else:
        print("No record of last scrape. Will scrape now.")

    if needs_scrape or not os.path.exists(PRODUCTS_FILE):
        print("Running scraper to fetch fresh product data...")
        # Call the scraper function from scraper.py
        products_data = run_scraper_and_get_data() # This will also save to apple_products.json
        if products_data: # Check if scraper returned any data
            set_last_scraped_time()
            print(f"Scraping complete. {len(products_data)} products loaded.")
            return products_data # Return the freshly scraped data
        elif os.path.exists(PRODUCTS_FILE): # If scraping failed but old file exists
             print("Scraping failed, but an old products file exists. Loading old data.")
             with open(PRODUCTS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        else: # Scraping failed and no old file
            print("Scraping failed and no existing products file. Returning empty list.")
            return []


    # If not needs_scrape and file exists
    if os.path.exists(PRODUCTS_FILE):
        try:
            with open(PRODUCTS_FILE, 'r', encoding='utf-8') as f:
                products = json.load(f)
                print(f"Loaded {len(products)} products from {PRODUCTS_FILE}")
                return products
        except json.JSONDecodeError:
            print(f"Error decoding JSON from {PRODUCTS_FILE}. Triggering re-scrape.")
            # Fallthrough to re-scrape logic essentially by returning result of run_scraper_and_get_data
            products_data = run_scraper_and_get_data()
            if products_data:
                set_last_scraped_time()
            return products_data if products_data else []
    else: # Should be caught by needs_scrape logic, but as a fallback
        print(f"{PRODUCTS_FILE} not found. Triggering scrape.")
        products_data = run_scraper_and_get_data()
        if products_data:
            set_last_scraped_time()
        return products_data if products_data else []


PRODUCTS = load_products()
if not PRODUCTS:
    print("Warning: No products loaded. The application might not function as expected.")
else:
    print(f"Total products loaded into app: {len(PRODUCTS)}")


def get_value_score(product):
    score = 0
    price = product.get('price_inr', float('inf'))
    if price == 0 or price == float('inf'): return 0 # Avoid division by zero or infinite scores

    # Weights - these can be tuned
    ram_weight = 25000  # Value per GB of RAM
    storage_weight = 50000 # Value per TB of SSD Storage
    cpu_core_weight = 7000 # Value per CPU core
    gpu_core_weight = 10000 # Value per GPU core
    # screen_size_weight = 1000 # Value per inch of screen (less critical for pure value)

    score += product.get('ram_gb', 0) * ram_weight
    score += product.get('storage_tb', 0) * storage_weight
    score += product.get('cpu_cores', 0) * cpu_core_weight
    score += product.get('gpu_cores', 0) * gpu_core_weight
    # score += product.get('screen_size_inch', 0) * screen_size_weight

    # Normalize by price: higher score for cheaper products with good specs
    # Adding 1 to price to avoid division by zero if price is somehow 0
    return score / (price + 1) if price > 0 else score


@app.route('/')
def index():
    # Sort products by price for the price ladder display
    sorted_products = sorted(PRODUCTS, key=lambda p: p.get('price_inr', float('inf')))
    return render_template('index.html', products=sorted_products)

@app.route('/find_products', methods=['POST'])
def find_products_api():
    data = request.get_json()
    budget = data.get('budget')

    if budget is None:
        return jsonify({"error": "Budget not provided"}), 400
    try:
        budget = float(budget)
    except ValueError:
        return jsonify({"error": "Invalid budget format"}), 400

    eligible_products = [p for p in PRODUCTS if p.get('price_inr') is not None and p.get('price_inr') <= budget]

    if not eligible_products:
        return jsonify([]) # Return empty list if no products meet budget

    # Sort by value score (descending) then by price (ascending) as a tie-breaker
    # best_value_products = sorted(
    #     eligible_products,
    #     key=lambda p: (get_value_score(p), -p.get('price_inr', 0)), # Higher score first, then lower price
    #     reverse=True
    # )
    # New strategy: most expensive product within budget
    best_value_products = sorted(
        eligible_products,
        key=lambda p: p.get('price_inr', 0),
        reverse=True # Most expensive first
    )


    # For now, let's return up to 5 best value products, or fewer if not many are eligible
    # Or just the top one if that's the desired behavior
    return jsonify(best_value_products[:5])


if __name__ == '__main__':
    if not PRODUCTS:
        print("CRITICAL: No products were loaded. The scraper might have failed and no previous data file was found.")
        print("Please check scraper.py output or run it manually (python scraper.py) to generate apple_products.json")
    app.run(host='0.0.0.0', port=10001, debug=True)