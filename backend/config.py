import os

# MongoDB Configuration
MONGO_URL = os.environ.get('MONGODB_URL')
MONGO_USER = os.environ.get('MONGODB_USER')
MONGO_PASSWORD = os.environ.get('MONGODB_PASSWORD')
MONGO_STOCK_URL_PROD = os.environ.get('MONGODB_STOCK_URL')
MONGO_STOCK_URL_DEV = os.environ.get('MONGODB_STOCK_URL_DEV')

# Flask Configuration
SECRET_KEY = os.environ.get('FLASK_SECRET_KEY')

# MongoDB URI
MONGO_URI_PROD = f"mongodb+srv://{MONGO_USER}:{MONGO_PASSWORD}@{MONGO_URL}/{MONGO_STOCK_URL_PROD}"
MONGO_URI_DEV = f"mongodb+srv://{MONGO_USER}:{MONGO_PASSWORD}@{MONGO_URL}/{MONGO_STOCK_URL_DEV}"

