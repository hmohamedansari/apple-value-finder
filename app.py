# app.py
import json
from flask import Flask, render_template, request, jsonify
import time
import os # Import the 'os' module to check file existence/modification time

# --- Import the scraper function ---
from scraper import scrape_apple_data, TARGET_URLS # Import the function and potentially the URLs list

# Initialize the Flask application
app = Flask(__name__)

# --- Configuration ---
DATA_FILE = 'apple_products.json' # Use the actual file name
# How often to re-scrape data (in seconds). 1 day = 86400 seconds. Let's use 6 hours for testing:
SCRAPE_INTERVAL = 6 * 60 * 60 # 6 hours
# Variable to hold the loaded product data in memory
product_data_cache = {
    "timestamp": 0,
    "products": []
}

# --- Helper Functions ---
def needs_scraping():
    """Checks if the data file is missing or older than SCRAPE_INTERVAL."""
    if not os.path.exists(DATA_FILE):
        print(f"{DATA_FILE} does not exist.")
        return True
    try:
        file_mod_time = os.path.getmtime(DATA_FILE)
        if time.time() - file_mod_time > SCRAPE_INTERVAL:
            print(f"{DATA_FILE} is older than {SCRAPE_INTERVAL / 3600} hours.")
            return True
        # Check if the file is empty or invalid JSON structure upon loading
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
             data = json.load(f)
             if not isinstance(data, dict) or "timestamp" not in data or "products" not in data or not data["products"]:
                  print(f"{DATA_FILE} is empty or has invalid format.")
                  return True # Re-scrape if empty or invalid format
    except (json.JSONDecodeError, IOError) as e:
         print(f"Error reading or decoding {DATA_FILE}: {e}")
         return True # Re-scrape if file is corrupt
    print(f"{DATA_FILE} is up-to-date.")
    return False

def load_product_data(force_scrape=False):
    """Loads product data, triggering scrape if needed or forced."""
    global product_data_cache
    if force_scrape or needs_scraping():
        print("Triggering scrape...")
        try:
            # Call the scraper function, saving to our main DATA_FILE
            scrape_apple_data(DATA_FILE)
        except Exception as e:
            print(f"!!! Scraping failed: {e} !!!")
            # Optional: Decide whether to proceed with potentially old data or stop
            # For now, we'll try to load whatever might be in the file anyway.
            pass # Continue to try loading the file

    # Always try to load the file after potential scrape attempt
    try:
        # Ensure using utf-8 encoding when reading
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Basic validation
            if isinstance(data, dict) and "timestamp" in data and "products" in data:
                product_data_cache = data
                print(f"Loaded {len(product_data_cache.get('products', []))} products from {DATA_FILE}")
            else:
                print(f"Warning: {DATA_FILE} has invalid format after load attempt. Cache remains empty.")
                product_data_cache = {"timestamp": 0, "products": []}
    except FileNotFoundError:
        print(f"Error: {DATA_FILE} not found after scrape attempt. Cache remains empty.")
        product_data_cache = {"timestamp": 0, "products": []}
    except json.JSONDecodeError:
        print(f"Error: Failed decoding JSON from {DATA_FILE}. Cache remains empty.")
        product_data_cache = {"timestamp": 0, "products": []}
    except Exception as e:
         print(f"An unexpected error occurred during data loading: {e}")
         product_data_cache = {"timestamp": 0, "products": []}


def get_value_score(product):
    """
    Calculates a value score based on scraped specs.
    Refined logic (v3) - higher score is better value.
    Increased weights for RAM/Storage/GPU significantly.
    """
    try:
        price = float(product.get('price_inr', 0))
        if price <= 0: return 0 # Avoid division by zero and invalid prices

        # --- Scoring Components (Adjust weights as desired - v3 Weights) ---
        # Chip Score: Base points for generation
        chip_score = 0
        chip = product.get('chip', '').upper()
        if 'M4' in chip: chip_score = 400 # Base for M4
        elif 'M3' in chip: chip_score = 300
        elif 'M2' in chip: chip_score = 200
        elif 'M1' in chip: chip_score = 100
        # Optional: Add points for Pro/Max/Ultra variants if needed later

        # CPU Core Score: Relatively lower weight
        cpu_cores = int(product.get('cpu_cores', 0))
        cpu_score = cpu_cores * 5 # Reduced weight (e.g., 5 points per core)

        # GPU Core Score: Increased weight
        gpu_cores = int(product.get('gpu_cores', 0))
        gpu_score = gpu_cores * 15 # Increased weight (e.g., 15 points per core)

        # RAM Score: Significantly increased weight
        ram_gb = int(product.get('ram_gb', 0))
        ram_score = ram_gb * 40 # Drastically increased (e.g., 40 points per GB)

        # Storage Score: Significantly increased weight
        storage_gb = int(product.get('storage_gb', 0))
        # Give more points per GB, especially for the jump from 256 to 512
        storage_score = storage_gb * 0.5 # Drastically increased (e.g., 0.5 points per GB)

        # --- Combine Scores ---
        # Summing up the component scores
        total_spec_score = chip_score + cpu_score + gpu_score + ram_score + storage_score

        # --- Final Value Score (Score per Rupee) ---
        # Normalize by price - higher score per rupee is better value
        # Multiply by 10000 or similar to get more manageable numbers
        value_score = (total_spec_score / price) * 10000 if price > 0 else 0

        # print(f"Score (v3 Weights) for {product.get('name')}: Specs={total_spec_score:.0f}, Price={price:.0f}, Value={value_score:.2f}") # Debug
        return value_score

    except Exception as e:
        print(f"Error calculating score for {product.get('name', 'Unknown')}: {e}")
        return 0 # Return 0 score if calculation fails

# Make sure the rest of app.py, including the find_best_value_products (v2) function

# app.py (Replace ONLY the find_best_value_products function)

def find_best_value_products(budget_inr):
    """
    Finds the most expensive product within budget and its neighbors. (Logic v3 - Option B)
    Includes debugging print statements.
    """
    print("\n--- Entering find_best_value_products (v3 - Option B) ---") # Debug Start
    print(f"Budget: ₹{budget_inr}") # Debug Budget

    if not product_data_cache or not product_data_cache.get('products'):
         print("DEBUG: No product data loaded in cache.")
         return None, None, None

    all_eligible_products = []
    print("DEBUG: Processing products from cache for eligibility:") # Debug
    for product in product_data_cache['products']:
        try:
            # Calculate value score for all eligible products first (still useful for context/potential future use)
            if not all(k in product for k in ['name', 'chip', 'price_inr', 'ram_gb', 'storage_gb']):
                 print(f"  - DEBUG Skipping product with missing keys: {product.get('name', 'Unknown')}")
                 continue
            price = float(product.get('price_inr', 0))
            if price > 0 and 'm' in product.get('chip', '').lower():
                product['value_score'] = get_value_score(product) # Keep calculating score
                if product['value_score'] > 0: # Ensure score is valid even if not primary sort key now
                     all_eligible_products.append(product)
        except (ValueError, TypeError) as e:
             print(f"  - DEBUG Skipping product due to data error: {product.get('name', 'Unknown')} - {e}")
             continue

    if not all_eligible_products:
        print("DEBUG: No eligible M-series products found after scoring.")
        return None, None, None

    print(f"\nDEBUG: Total eligible products found: {len(all_eligible_products)}")

    # --- Step 1: Filter products within budget ---
    products_within_budget = [
        p for p in all_eligible_products if float(p.get('price_inr', float('inf'))) <= budget_inr
    ]
    print(f"\nDEBUG: Products within budget (≤ ₹{budget_inr}): {len(products_within_budget)}")

    # --- Step 2: Find MOST EXPENSIVE *among* those within budget ---
    best_match = None
    if products_within_budget:
        # Sort the within-budget products by PRICE (desc) to find the most expensive
        products_within_budget.sort(key=lambda p: float(p.get('price_inr', 0)), reverse=True) # Sort by PRICE desc
        best_match = products_within_budget[0] # Highest price within budget
        print(f"\nDEBUG: Best match search (Highest price within budget - Option B):")
        print(f"  -> DEBUG Selected best match: {best_match['name']} (Score: {best_match.get('value_score', 0):.2f}, Price: ₹{best_match['price_inr']})")
    else:
        # Handle case where nothing is within budget - find cheapest overall (remains the same)
        print(f"\nDEBUG: No products found within budget ₹{budget_inr}. Finding cheapest overall M-series.")
        all_eligible_products.sort(key=lambda p: float(p.get('price_inr', float('inf')))) # Sort all by price asc
        best_match = all_eligible_products[0] if all_eligible_products else None
        if best_match:
             print(f"  -> DEBUG Selected cheapest overall as best match: {best_match['name']} (Price: ₹{best_match['price_inr']})")
        else:
             print("  -> DEBUG Still no products found even when looking for cheapest.")
             return None, None, None # Still nothing

    # --- Step 3: Find neighbors based on PRICE in the *full* list ---
    # This part remains the same - neighbors are always based on the full price-sorted list
    print("\nDEBUG: Finding neighbors based on PRICE (using full eligible list):")
    # Sort *all* eligible M-series products by price (ascending)
    all_eligible_products.sort(key=lambda p: float(p.get('price_inr', float('inf'))))
    print("DEBUG: Full eligible products sorted by PRICE (asc):") # Debug Sort Price
    for i, p in enumerate(all_eligible_products): print(f"  {i}: {p['name']} (Price: ₹{p.get('price_inr', 0)})")

    best_match_index = -1
    try:
        # Find the index of the actual best_match object in the full price-sorted list
        best_match_index = all_eligible_products.index(best_match)
    except ValueError:
        print("  - DEBUG Warning: best_match object not found directly in price-sorted list. Trying name/price match.")
        for i, product in enumerate(all_eligible_products):
             if product['name'] == best_match['name'] and product['price_inr'] == best_match['price_inr']:
                 best_match_index = i
                 break

    print(f"\nDEBUG: Index of best match ('{best_match['name']}') in full price-sorted list: {best_match_index}") # Debug Index

    if best_match_index == -1:
         print("DEBUG Error: Could not re-locate best_match in full price-sorted list.")
         return best_match, None, None # Fallback

    # Select neighbors based on the found index in the full list
    cheaper_neighbor = all_eligible_products[best_match_index - 1] if best_match_index > 0 else None
    expensive_neighbor = all_eligible_products[best_match_index + 1] if best_match_index < len(all_eligible_products) - 1 else None

    print(f"DEBUG: Cheaper neighbor selected: {cheaper_neighbor['name'] if cheaper_neighbor else 'None'}") # Debug Cheaper
    print(f"DEBUG: Expensive neighbor selected: {expensive_neighbor['name'] if expensive_neighbor else 'None'}") # Debug Expensive
    print("--- Exiting find_best_value_products (v3 - Option B) ---") # Debug End

    return best_match, cheaper_neighbor, expensive_neighbor

# Make sure the get_value_score function (with v3 weights) and the rest of app.py remain unchanged.
# Also, ensure you only have ONE definition of find_best_value_products in the file.

# Rest of app.py remains the same

# --- Routes ---
@app.route('/', methods=['GET'])
def index():
    """Renders the main page. Data loading is handled on startup/API call."""
    # Data loading now happens primarily on startup and in the API call if needed
    return render_template('index.html')

@app.route('/find_value', methods=['POST'])
def find_value_api():
    """API endpoint to find products based on budget."""
    try:
        # Ensure data is loaded (especially if app restarted or cache cleared)
        # Run load_product_data() which includes the check/scrape logic
        if not product_data_cache or not product_data_cache.get('products'):
             print("API call found empty cache, attempting to load/scrape data...")
             load_product_data() # This will scrape only if necessary

        # Check again if data loading failed
        if not product_data_cache or not product_data_cache.get('products'):
             print("API call failed: No product data available after load attempt.")
             return jsonify({"error": "Product data is currently unavailable. Please try again later."}), 503 # Service Unavailable

        data = request.get_json()
        budget_str = data.get('budget')
        if not budget_str:
            return jsonify({"error": "Budget not provided"}), 400

        budget_inr = float(budget_str)
        if budget_inr <= 0:
             return jsonify({"error": "Budget must be positive"}), 400

        best_match, cheaper, expensive = find_best_value_products(budget_inr)

        return jsonify({
            "best_match": best_match,
            "cheaper_alternative": cheaper,
            "expensive_alternative": expensive
        })

    except ValueError:
        return jsonify({"error": "Invalid budget amount"}), 400
    except Exception as e:
        print(f"Error in /find_value: {e}") # Log the error server-side
        # import traceback # Uncomment for detailed stack trace
        # traceback.print_exc() # Uncomment for detailed stack trace
        return jsonify({"error": "An internal error occurred"}), 500

# app.py (Add this new function)

@app.route('/products', methods=['GET'])
def get_all_products():
    """API endpoint to get all available products, sorted by price."""
    try:
        # Ensure data is loaded (especially if app restarted or cache cleared)
        if not product_data_cache or not product_data_cache.get('products'):
             print("API call (/products) found empty cache, attempting to load/scrape data...")
             load_product_data() # This will scrape only if necessary

        # Check again if data loading failed
        if not product_data_cache or not product_data_cache.get('products'):
             print("API call (/products) failed: No product data available after load attempt.")
             return jsonify({"error": "Product data is currently unavailable."}), 503

        # Get a copy of the products and sort them by price (ascending)
        products = list(product_data_cache.get('products', []))
        # Ensure price is treated as float for sorting, handle potential errors
        products.sort(key=lambda p: float(p.get('price_inr', float('inf'))))

        print(f"API call (/products): Returning {len(products)} products sorted by price.")
        return jsonify(products)

    except Exception as e:
        print(f"Error in /products: {e}") # Log the error server-side
        return jsonify({"error": "An internal error occurred"}), 500

# Keep the existing '/' route for rendering index.html
# Keep the existing '/find_value' route for now, although the new design won't use it.
# Keep the main execution block (__name__ == '__main__')

# --- Main Execution ---
if __name__ == '__main__':
    print("Application starting...")
    load_product_data() # Load data on startup (will scrape if needed)
    # Run the Flask app
    print(f"Starting Flask server on host 0.0.0.0, port 10001 with debug mode {'on' if app.debug else 'off'}")
    app.run(debug=True, host='0.0.0.0', port=10001) # Use the working port