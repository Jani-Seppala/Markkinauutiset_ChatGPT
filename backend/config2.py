import os
import redis
from pymongo import MongoClient
from flask_pymongo import PyMongo
from flask import Flask
import logging
from flask_socketio import SocketIO
import urllib.parse

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def create_app():
    app = Flask(__name__)
    app.config["MONGO_URI"] = os.getenv('MONGODB_URI_PROD') if os.getenv('FLASK_ENV') == 'production' else os.getenv('MONGODB_URI_DEV')
    app.config["SECRET_KEY"] = os.getenv('FLASK_SECRET_KEY')
    logging.info("Flask app created with MONGO_URI: {} and SECRET_KEY: {}".format(app.config["MONGO_URI"], app.config["SECRET_KEY"]))
    return app

def get_mongo_client():
    mongo_uri = os.getenv('MONGODB_URI_PROD') if os.getenv('FLASK_ENV') == 'production' else os.getenv('MONGODB_URI_DEV')
    if mongo_uri is None:
        logging.error("MongoDB URI is not set.")
    else:
        # logging.info(f"Using MongoDB URI: {mongo_uri}")
        logging.info(f"MongoDB connection URI fetched successfully.")
    return MongoClient(mongo_uri)

def get_redis_client():
    # redis_host = os.getenv('REDIS_HOST', 'localhost')
    # redis_port = int(os.getenv('REDIS_PORT', 6379))
    # redis_db = int(os.getenv('REDIS_DB', 0))
    redis_host = os.getenv('REDIS_HOST')
    redis_port = int(os.getenv('REDIS_PORT'))
    redis_db = int(os.getenv('REDIS_DB'))
    redis_password = os.getenv('REDIS_PASSWORD', None)
    # pool = redis.ConnectionPool(host=redis_host, port=redis_port, db=redis_db, password=redis_password, socket_timeout=5)
    # return redis.StrictRedis(connection_pool=pool)
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
    # message_queue = os.getenv('REDIS_URL', 'redis://localhost:6379') if os.getenv('FLASK_ENV') == 'production' else None
    redis_host = os.getenv('REDIS_HOST', 'localhost')
    redis_port = int(os.getenv('REDIS_PORT', '6379'))
    redis_db = int(os.getenv('REDIS_DB', '0'))
    redis_password = os.getenv('REDIS_PASSWORD', None)
    encoded_password = urllib.parse.quote_plus(redis_password)
    # redis_url = f"redis://:{redis_password}@{redis_host}:{redis_port}/{redis_db}"
    redis_url = f"redis://:{encoded_password}@{redis_host}:{redis_port}/{redis_db}"
    logging.info(redis_url)
    
    # message_queue = None
    # message_queue = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    logging.info("Initializing SocketIO with eventlet and CORS settings...")
    
    try:
        # socketio = SocketIO(app, async_mode='eventlet', cors_allowed_origins="*", logger=True, engineio_logger=True, message_queue=message_queue)
        # socketio = SocketIO(app, async_mode='eventlet', cors_allowed_origins="*", logger=True, engineio_logger=True, message_queue=redis_url)
        socketio = SocketIO(app, async_mode='eventlet', cors_allowed_origins=cors_allowed_origins, logger=True, engineio_logger=True, message_queue=redis_url)
        logging.info("SocketIO initialized successfully with eventlet. and message_queue: {}".format(redis_url))
    except Exception as e:
        logging.error("Failed to initialize SocketIO: {}".format(e))
        raise
    
    return socketio

def get_flask_pymongo(app):
    return PyMongo(app)
