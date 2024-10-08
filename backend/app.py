import eventlet
eventlet.monkey_patch()  # Patch the standard library to be non-blocking

from flask import request, redirect, url_for, flash, jsonify, session, send_from_directory
# from flask_pymongo import PyMongo
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_socketio import SocketIO
from bson.objectid import ObjectId
from flask_cors import CORS
from bson import json_util
from datetime import timedelta
# from config2 import create_app, get_flask_pymongo, create_socketio, get_redis_client
from config2 import create_app, get_flask_pymongo, create_socketio
# import redis
import bcrypt
import subprocess
import sys
import os
import logging
import time

app = create_app()
mongo = get_flask_pymongo(app)
socketio = create_socketio(app)

# app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY')
# app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=30)
# app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(minutes=1)
# jwt = JWTManager(app)

# Enable CORS for the entire app
# CORS(app)

# Basic configuration for logging
logging.basicConfig(level=logging.INFO,  # You can change this to DEBUG for more verbose output
                    format='%(asctime)s:%(levelname)s:%(message)s')


logging.info("Application is starting...")
logging.info(f"Environment: {os.getenv('FLASK_ENV')}")


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    if path and os.path.exists(os.path.join(app.static_folder, '..', path)):
        return send_from_directory('frontend/build', path)
    else:
        return send_from_directory('frontend/build', 'index.html')


@app.route('/api/users/register', methods=['POST'])
def register_user():
    users = mongo.db.users
    existing_user = users.find_one({'email': request.json['email']})

    if existing_user is None:
        # Mandatory fields
        first_name = request.json['first_name']
        last_name = request.json['last_name']
        email = request.json['email']
        password = request.json['password']
        
        # Optional fields
        address = request.json.get('address', '')
        country = request.json.get('country', '')
        phone = request.json.get('phone', '')

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        # Create user document including optional fields if provided
        user_data = {
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'password': hashed_password,
            'favorites': []
        }
        
        # Only add optional fields to document if they are not empty
        if address: user_data['address'] = address
        if country: user_data['country'] = country
        if phone: user_data['phone'] = phone

        # Insert the new user document into the collection
        users.insert_one(user_data)

        return jsonify({"success": True, "message": "User registered successfully"})
    else:
        return jsonify({"success": False, "message": "Email is already registered."})


@app.route('/api/users/login', methods=['POST'])
def login():
    users = mongo.db.users
    login_user = users.find_one({'email': request.json['email']})

    if login_user:
        hashed_password = login_user['password']
        password_check = bcrypt.checkpw(request.json['password'].encode('utf-8'), hashed_password)
        if password_check:
            # Set the token to expire in 1 hour
            access_token = create_access_token(identity=str(login_user['_id']))
            # Convert the ObjectId to a string before returning the user data
            login_user['_id'] = str(login_user['_id'])
            # Remove the password before returning the user data
            login_user.pop('password')
            return jsonify({"success": True, "message": f"Welcome back, {login_user['first_name']}!", "token": access_token, "user": login_user})
        else:
            return jsonify({"success": False, "message": "Invalid login credentials."}), 401
    else:
        return jsonify({"success": False, "message": "Invalid login credentials."}), 401


@app.route('/api/users/<user_id>/add_favorite/<stock_id>', methods=['POST'])
@jwt_required()
def add_favorite(user_id, stock_id):
    if get_jwt_identity() != user_id:
        logging.error("Attempt to access without valid user id")
        return jsonify({"error": "Unauthorized"}), 403
    user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
    if stock_id in user.get("favorites", []):
        logging.error(f"Stock is already in the favorites for user {user_id}")
        return jsonify({"message": "Stock is already in favorites"}), 409
    try:
        mongo.db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$addToSet": {"favorites": stock_id}}
        )
        logging.info(f"Updated favorites for user {user_id}")
        return jsonify({"message": "Stock added to favorites"}), 200
    except Exception as e:
        logging.exception("Failed to update favorites due to an error.")
        return jsonify({"error": str(e)}), 500



@app.route('/api/favorites', methods=['GET'])
@jwt_required()
def get_favorites():
    user_id = get_jwt_identity()  # Get user ID from the JWT payload
    user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
    if user and 'favorites' in user:
        # Convert strings in the favorites list to ObjectIds
        favorites_ids = [ObjectId(favorite) for favorite in user['favorites']]
        # Fetch the full details of each favorite stock
        favorites_info = list(mongo.db.stocks.find({"_id": {"$in": favorites_ids}}))
        # Convert ObjectIds in the favorites_info to strings
        for favorite in favorites_info:
            favorite['_id'] = str(favorite['_id'])
        return jsonify(favorites_info)
    else:
        return jsonify({"error": "User not found"}), 404


@app.route('/api/favorites', methods=['POST'])
@jwt_required()
def update_favorites():
    user_id = get_jwt_identity()  # Get user ID from the JWT payload
    user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
    if user:
        favorites = request.json.get('favorites', [])
        mongo.db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"favorites": favorites}}
        )
        return jsonify({"message": "Favorites updated successfully!"})
    else:
        return jsonify({"error": "User not found"}), 404



# Logout Route
@app.route('/logout')
def logout():
    # Clear the user session
    session.clear()
    # Flash a message indicating the user has been logged out
    flash('You have been successfully logged out.', 'info')
    return redirect(url_for('index'))


# Get all stocks for search bar
@app.route('/api/stocks')
def get_stocks():
    search_query = request.args.get('query', '')  # Retrieve the search query parameter
    if search_query:
        # Perform a case-insensitive search for stocks matching the query
        stocks = mongo.db.stocks.find({"name": {"$regex": search_query, "$options": "i"}})
    else:
        # If no query is provided, return all stocks
        stocks = mongo.db.stocks.find()
    
    stocks_list = list(stocks)
    # Convert ObjectId() to string because it is not JSON serializable
    for stock in stocks_list:
        stock['_id'] = str(stock['_id'])
    return jsonify(stocks_list)


# Get a single stock by its ID
@app.route('/api/stocks/<stockId>', methods=['GET'])
def get_stock(stockId):
    try:
        stock = mongo.db.stocks.find_one({"_id": ObjectId(stockId)})
        if stock:
            # Convert the _id from ObjectId to string for JSON serialization
            stock['_id'] = str(stock['_id'])
            return jsonify(stock), 200
        else:
            return jsonify({"error": "Stock not found"}), 404
    except Exception as e:
        return jsonify({"error": "An error occurred", "details": str(e)}), 500


# @app.route('/api/news-with-analysis', methods=['GET'])
# def get_news_with_analysis():
#     stock_id = request.args.get('stock_id')
#     stock_ids = request.args.get('stock_ids')
#     markets = request.args.getlist('market')
#     page = int(request.args.get('page', 1))
#     limit = 10
#     actual_fetch_limit = limit + 1
#     # Adjust the skip to account for the extra news item
#     skip = (page - 1) * limit
    
#     print(f"{limit=}")
#     print(f"{skip=}")

#     # Build the query based on the provided parameters
#     if stock_id:
#         # Fetch news for the specified stock, sorted by releaseTime
#         query = {"stock_id": ObjectId(stock_id)}
#     elif stock_ids:
#         # Fetch news for multiple specified stocks, sorted by releaseTime
#         stock_ids_list = stock_ids.split(',')
#         stock_object_ids = [ObjectId(id) for id in stock_ids_list]
#         query = {"stock_id": {"$in": stock_object_ids}}
#     else:
#         # Fetch all news, sorted by releaseTime
#         query = {}

#     if markets:
#         # Map 'finnish' and 'swedish' to actual market names
#         market_mapping = {
#             'finnish': ["First North Finland", "Main Market, Helsinki"],
#             'swedish': ["First North Sweden", "Main Market, Stockholm"]
#         }
#         actual_markets = []
#         for m in markets:
#             actual_markets.extend(market_mapping.get(m, []))
#         query["market"] = {"$in": actual_markets}

#     # Apply the query, sorting, pagination, and conversion to a list
#     news_items = list(mongo.db.news.find(query).sort([
#         ('releaseTime', -1), 
#         ("company", 1), 
#         ("_id", 1)
#     ]).skip(skip).limit(actual_fetch_limit))
    
#     print(f"Page: {page}, Limit: {limit}, Skip: {skip}")
#     print("News IDs returned:", [item['_id'] for item in news_items])
    
#     has_more = len(news_items) > limit  # Check if there are more items than the limit
#     displayed_items = news_items[:limit]  # Only send 'limit' items to the frontend

#     result = [{
#         "news": item,
#         "analysis": mongo.db.analysis.find_one({"news_id": item["_id"]})
#     } for item in displayed_items]
        
        
#     print(f"{len(result)} result pituus")
    
#     result_json = json_util.dumps({"items": result, "has_more": has_more})
#     return app.response_class(response=result_json, mimetype='application/json')


# @app.route('/api/users/me', methods=['GET'])
# @jwt_required()
# def get_logged_in_user():
#     user_id = get_jwt_identity()
#     user = mongo.db.users.find_one({"_id": ObjectId(user_id)})

#     if user:
#         # Convert ObjectId to string
#         user['_id'] = str(user['_id'])
#         # Remove the password before returning the user data
#         user.pop('password')
#         return jsonify({"success": True, "user": user})
#     else:
#         return jsonify({"success": False, "message": "User not found."}), 404


@app.route('/api/news-with-analysis', methods=['GET'])
def get_news_with_analysis():
    stock_id = request.args.get('stock_id')
    stock_ids = request.args.get('stock_ids')
    markets = request.args.getlist('market')
    page = int(request.args.get('page', 1))
    limit = 10
    actual_fetch_limit = limit + 1
    skip = (page - 1) * limit

    print(f"{limit=}")
    print(f"{skip=}")

    # Build the query based on the provided parameters
    if stock_id:
        # Fetch news for the specified stock
        query = {"stock_id": ObjectId(stock_id)}
    elif stock_ids:
        # Fetch news for multiple specified stocks
        stock_ids_list = stock_ids.split(',')
        stock_object_ids = [ObjectId(id) for id in stock_ids_list]
        query = {"stock_id": {"$in": stock_object_ids}}
    else:
        # Fetch all news
        query = {}

    if markets:
        # Map 'finnish' and 'swedish' to actual market names
        market_mapping = {
            'finnish': ["First North Finland", "Main Market, Helsinki"],
            'swedish': ["First North Sweden", "Main Market, Stockholm"]
        }
        actual_markets = []
        for m in markets:
            actual_markets.extend(market_mapping.get(m, []))
        query["market"] = {"$in": actual_markets}

    # Use aggregation pipeline to group by 'relatedId' and remove duplicates
    pipeline = [
        {'$match': query},
        {'$sort': {'releaseTime': -1, 'company': 1, '_id': 1}},
        {'$group': {
            '_id': '$relatedId',  # Group by 'relatedId'
            'news_item': {'$first': '$$ROOT'}  # Take the first document in each group
        }},
        {'$sort': {
            'news_item.releaseTime': -1,
            'news_item.company': 1,
            'news_item._id': 1
        }},
        {'$skip': skip},
        {'$limit': actual_fetch_limit}
    ]


    # TRY THIS PIPELINE IF THERE IS PROBLEM WITH THE CURRENT ONE!!!
    # pipeline = [
    #     {'$match': query},
    #     {'$sort': {'releaseTime': -1, 'company': 1, '_id': 1}},
    #     {'$group': {
    #         '_id': {
    #             '$ifNull': [
    #                 '$relatedId',
    #                 {
    #                     '$ifNull': [
    #                         '$disclosureId',
    #                         {'company': '$company', 'headline': '$headline', 'releaseTime': '$releaseTime'}
    #                     ]
    #                 }
    #             ]
    #         },
    #         'news_item': {'$first': '$$ROOT'}
    #     }},
    #     {'$sort': {
    #         'news_item.releaseTime': -1,
    #         'news_item.company': 1,
    #         'news_item._id': 1
    #     }},
    #     {'$skip': skip},
    #     {'$limit': actual_fetch_limit}
    # ]


    # Execute the aggregation pipeline
    aggregated_news = list(mongo.db.news.aggregate(pipeline))

    print(f"Page: {page}, Limit: {limit}, Skip: {skip}")
    print("News IDs returned:", [item['news_item']['_id'] for item in aggregated_news])

    has_more = len(aggregated_news) > limit  # Check if there are more items than the limit
    displayed_items = aggregated_news[:limit]  # Only send 'limit' items to the frontend

    result = [{
        "news": item['news_item'],
        "analysis": mongo.db.analysis.find_one({"news_id": item['news_item']['_id']})
    } for item in displayed_items]

    print(f"{len(result)} result pituus")

    result_json = json_util.dumps({"items": result, "has_more": has_more})
    return app.response_class(response=result_json, mimetype='application/json')


#used only in development, production has its own redis_listener.py
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
    env = os.getenv('FLASK_ENV', 'development')
    
    if env == 'development':
        from config2 import get_redis_client
        redis_client = get_redis_client()
        
        logging.info("Development environment detected. calling nasdaqapicall from app.py")
        try:
            subprocess.Popen([sys.executable, '-m', 'apicalls.nasdaqApiCall'])
        except Exception as e:
            logging.error(f"Failed to start the scheduler: {str(e)}")
    
        eventlet.spawn(listen_to_redis)
        socketio.run(app, debug=True, use_reloader=False)
        # socketio.run(app, debug=True, use_reloader=True)
