import eventlet
eventlet.monkey_patch()  # Patch the standard library to be non-blocking

from config2 import create_app, create_socketio, get_redis_client

app = create_app()
socketio = create_socketio(app)
redis_client = get_redis_client()

def listen_to_redis():
    pubsub = redis_client.pubsub()
    pubsub.subscribe('news_channel')
    while True:
        message = pubsub.get_message()
        if message:
            if message['type'] == 'message':
                print("Received message:", message['data'])
                socketio.emit('update_news', {'message': message['data'].decode()})
        eventlet.sleep(0.1)  # Short sleep to yield control

if __name__ == "__main__":
    listen_to_redis()
