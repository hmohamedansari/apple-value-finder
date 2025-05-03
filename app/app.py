import os
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from flask_migrate import Migrate

# Import database instance and models
from .models import db, Product, Configuration

load_dotenv() # Load environment variables from .env file

def create_app():
    app = Flask(__name__)

    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'a_default_secret_key') # Change in production
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize extensions
    db.init_app(app)
    Migrate(app, db) # Initialize Flask-Migrate

    # --- Routes ---
    @app.route('/')
    def index():
        """Render the main page."""
        return render_template('index.html')

    @app.route('/api/find-by-budget', methods=['GET'])
    def find_by_budget():
        """API endpoint to find products based on budget."""
        try:
            budget_str = request.args.get('amount', '0')
            budget_inr = int(float(budget_str)) # Handle potential float input
        except ValueError:
            return jsonify({"error": "Invalid budget amount"}), 400

        # --- Placeholder Logic (Replace with actual DB query and value logic) ---
        # Query database for products <= budget, slightly below, slightly above
        # For now, just return the budget
        results = {
            "budget_received": budget_inr,
            "best_fit": [], # Populate with product dicts
            "cheaper_options": [], # Populate with product dicts
            "pricier_options": [] # Populate with product dicts
        }
        # TODO: Implement database query and sorting logic here
        # Example structure for a product dict:
        # { "name": "MacBook Air M2", "chip": "M2", "ram": 8, "storage": 256, "price": 95000, "image_url": "...", "type": "MacBook" }

        return jsonify(results)

    # --- Add more routes as needed ---

    return app

# This allows running `flask run` directly
if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0') # Runs on port 5000 by default