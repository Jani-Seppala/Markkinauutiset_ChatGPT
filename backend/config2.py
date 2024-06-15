import os
from pymongo import MongoClient
from flask_pymongo import PyMongo
from flask import Flask
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def create_app():
    app = Flask(__name__)
    app.config["MONGO_URI"] = os.getenv('MONGODB_URI_PROD') if os.getenv('FLASK_ENV') == 'production' else os.getenv('MONGODB_URI_DEV')
    app.config["SECRET_KEY"] = os.getenv('FLASK_SECRET_KEY')
    return app

def get_mongo_client():
    mongo_uri = os.getenv('MONGODB_URI_PROD') if os.getenv('FLASK_ENV') == 'production' else os.getenv('MONGODB_URI_DEV')
    if mongo_uri is None:
        logging.error("MongoDB URI is not set.")
    else:
        logging.info(f"Using MongoDB URI: {mongo_uri}")
    return MongoClient(mongo_uri)

def get_flask_pymongo(app):
    return PyMongo(app)
