# pages/__init__.py
from flask import Blueprint

# Create the revenue blueprint
revenue_blueprint = Blueprint('revenue', __name__)
products_blueprint = Blueprint('products', __name__)

