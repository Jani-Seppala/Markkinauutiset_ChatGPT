# import eventlet
# eventlet.monkey_patch()  # Patch the standard library to be non-blocking

# from config2 import create_app, create_socketio, get_redis_client

# app = create_app()
# socketio = create_socketio(app)
# redis_client = get_redis_client()

# def listen_to_redis():
#     pubsub = redis_client.pubsub()
#     pubsub.subscribe('news_channel')
#     while True:
#         message = pubsub.get_message()
#         if message:
#             if message['type'] == 'message':
#                 print("Received message:", message['data'])
#                 socketio.emit('update_news', {'message': message['data'].decode()})
#         eventlet.sleep(0.1)  # Short sleep to yield control

# if __name__ == "__main__":
#     listen_to_redis()

import eventlet

eventlet.monkey_patch()  # Patch the standard library to be non-blocking
import logging
from config2 import create_app, create_socketio, get_redis_client

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# app = create_app()
# socketio = create_socketio(app)
socketio = create_socketio()
redis_client = get_redis_client()

def listen_to_redis():
    logging.info("listen_to_redis function reached")
    pubsub = redis_client.pubsub()
    try:
        pubsub.subscribe('news_channel')
        logging.info("Subscribed to Redis channel 'news_channel'")
    except Exception as e:
        logging.error("Failed to subscribe to 'news_channel': {}".format(e))
        return

    logging.info("Entering the message listening loop...")
    # while True:
    #     try:
    #         message = pubsub.get_message()
    #         if message and message['type'] == 'message':
    #             logging.info("Received message: {}".format(message['data']))
    #             socketio.emit('update_news', {'message': message['data'].decode()})
    #         eventlet.sleep(0.1)  # Short sleep to yield control
    #     except Exception as e:
    #         logging.error("Error processing message: {}".format(e))
    
    while True:
        try:
            message = pubsub.get_message()
            if message:
                logging.info(f"Polled message from Redis: {message}")  # Log every poll attempt regardless of message type
                if message['type'] == 'message':
                    logging.info(f"Received message: {message['data']}")
                    socketio.emit('update_news', {'message': message['data'].decode()})
                    logging.info(f"Emitted message to front-end: {message['data']}")
            eventlet.sleep(0.1)  # Short sleep to yield control
        except Exception as e:
            logging.error(f"Error processing message: {e}")

if __name__ == "__main__":
    listen_to_redis()
