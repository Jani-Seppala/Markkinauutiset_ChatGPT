import os
import redis
from pymongo import MongoClient
from flask_pymongo import PyMongo
from flask import Flask
import logging
from flask_socketio import SocketIO
from flask_jwt_extended import JWTManager
from datetime import timedelta
from flask_cors import CORS
import urllib.parse

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def create_app():
    app = Flask(__name__)
    app.config["MONGO_URI"] = os.getenv('MONGODB_URI_PROD') if os.getenv('FLASK_ENV') == 'production' else os.getenv('MONGODB_URI_DEV')
    app.config["SECRET_KEY"] = os.getenv('FLASK_SECRET_KEY')
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=30)
    JWTManager(app)
    
    # Configure CORS based on the environment
    if os.getenv('FLASK_ENV') == 'production':
        cors_origins = ["https://www.ainewsanalyzer.com", "https://ainewsanalyzer.com"]
    else:
        cors_origins = ['http://localhost:3000']  # Localhost for development
    
    # Initialize CORS with more specific settings
    CORS(app, origins=cors_origins, methods=["GET", "POST", "PUT", "DELETE"], 
         allow_headers=["Content-Type", "Authorization", "X-Requested-With"])
    
    logging.info("Flask app created with MONGO_URI: {} and SECRET_KEY: {}".format(app.config["MONGO_URI"], app.config["SECRET_KEY"]))
    return app


def get_mongo_client():
    mongo_uri = os.getenv('MONGODB_URI_PROD') if os.getenv('FLASK_ENV') == 'production' else os.getenv('MONGODB_URI_DEV')
    if mongo_uri is None:
        logging.error("MongoDB URI is not set.")
    else:
        logging.info(f"MongoDB connection URI fetched successfully.")
    return MongoClient(mongo_uri)

def get_redis_client():
    redis_host = os.getenv('REDIS_HOST')
    redis_port = int(os.getenv('REDIS_PORT'))
    redis_db = int(os.getenv('REDIS_DB'))
    redis_password = os.getenv('REDIS_PASSWORD', None)
    try:
        pool = redis.ConnectionPool(host=redis_host, port=redis_port, db=redis_db, password=redis_password, socket_timeout=5)
        redis_client = redis.StrictRedis(connection_pool=pool)
        redis_client.ping()  # Test the connection
        logging.info(f"Connected to Redis at {redis_host}:{redis_port}/{redis_db}")
    except Exception as e:
        logging.error(f"Failed to connect to Redis: {e}")
        raise ConnectionError("Failed to connect to Redis")
    
    return redis_client

def create_socketio(app=None):
    cors_allowed_origins = ["https://www.ainewsanalyzer.com", "https://ainewsanalyzer.com"] if os.getenv('FLASK_ENV') == 'production' else ["http://localhost:3000"]
    redis_host = os.getenv('REDIS_HOST', 'localhost')
    redis_port = int(os.getenv('REDIS_PORT', '6379'))
    redis_db = int(os.getenv('REDIS_DB', '0'))
    redis_password = os.getenv('REDIS_PASSWORD', None)
    encoded_password = urllib.parse.quote_plus(redis_password)
    redis_url = f"redis://:{encoded_password}@{redis_host}:{redis_port}/{redis_db}"
    logging.info(redis_url)
    logging.info("Initializing SocketIO with eventlet and CORS settings...")
    
    try:
        socketio = SocketIO(app, async_mode='eventlet', cors_allowed_origins=cors_allowed_origins, logger=True, engineio_logger=True, message_queue=redis_url)
        logging.info("SocketIO initialized successfully with eventlet. and message_queue: {}".format(redis_url))
    except Exception as e:
        logging.error("Failed to initialize SocketIO: {}".format(e))
        raise
    
    return socketio

def get_flask_pymongo(app):
    return PyMongo(app)
