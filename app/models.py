from flask_sqlalchemy import SQLAlchemy
import datetime

db = SQLAlchemy() # Initialize SQLAlchemy

class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False) # e.g., "MacBook Air 13-inch"
    product_type = db.Column(db.String(50), nullable=False) # 'MacBook', 'iPad'
    screen_size = db.Column(db.Float, nullable=True) # e.g., 13.6
    base_image_url = db.Column(db.String(255), nullable=True) # URL for a representative image
    apple_url = db.Column(db.String(255), nullable=True, unique=True) # Link to product page
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    configurations = db.relationship('Configuration', backref='product', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Product {self.name}>'

class Configuration(db.Model):
    __tablename__ = 'configurations'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    chip = db.Column(db.String(50), nullable=False) # e.g., "M2", "M3 Pro"
    ram_gb = db.Column(db.Integer, nullable=False) # e.g., 8, 16
    storage_gb = db.Column(db.Integer, nullable=False) # e.g., 256, 512
    price_inr = db.Column(db.Integer, nullable=False) # Store price as integer (paise) or use Numeric type if needed
    color = db.Column(db.String(50), nullable=True) # Optional: 'Space Grey', 'Silver'
    sku = db.Column(db.String(100), nullable=True, unique=True) # Apple SKU if available
    last_scraped_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    def __repr__(self):
        return f'<Config {self.product.name} - {self.chip}/{self.ram_gb}GB/{self.storage_gb}GB - ₹{self.price_inr}>'