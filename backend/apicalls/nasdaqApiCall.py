import requests
import datetime
import pytz
import time
from uuid import uuid4
from bs4 import BeautifulSoup
import re
import os
import sys
import schedule
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config2 import get_mongo_client, get_redis_client

from apicalls.YahooFinanceApiCall import main as fetch_stock_data
from apicalls.openAiApiCall import analyze_news

# redis_client = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)
redis_client = get_redis_client()

logging.info('Starting nasdaqApiCall.py')

def fetch_news(url):
    """ Fetch news from a given URL and process it if successful. """
    response = requests.get(url)
    if response.status_code == 200:
        logging.info(f"News fetched successfully.at {datetime.datetime.now(pytz.timezone('Europe/Stockholm')).strftime('%Y-%m-%d %H:%M:%S')} from {url}")
        news_data = response.json().get('results', {}).get('item', [])
        # preprocess_news_items(news_data[:3])  # Process only the first 2 news item
        preprocess_news_items(news_data)
        # exit(0)  # Exit after processing the first item
        return
    else:
        logging.info(f"Failed to fetch news: {response.status_code}")


def extract_manager_name(headline):
    """Return an empty string if the headline ends with specified phrases, indicating no manager name."""
    # Check if the headline ends with the specified phrases.
    if headline.strip().endswith("- Managers' Transactions") or headline.strip().endswith("- Johdon liiketoimet"):
        return ""
    
    """Attempt to extract manager's name from the headline using regex."""
    patterns = [r'[-:]\s*([A-Za-zäöüßÄÖÜẞ\s]+)$', r'\(([A-Za-zäöüßÄÖÜẞ\s]+)\)']
    for pattern in patterns:
        match = re.search(pattern, headline)
        if match:
            return match.group(1).strip()
    return ""


def preprocess_news_items(news_items):
    """Group news items by company and timestamp, modifying the disclosureId to include the language."""
    processed_items = []

    for item in news_items:
        languages = item.get('languages', [item.get('language')])  # Default to the current item's language if 'languages' is not set

        # Process each language for the news item
        for lang in languages:
            new_item = item.copy()  # Create a shallow copy of the item

            # Generate a new, modified disclosureId for the item including the language
            new_item['disclosureId'] = f"{item['disclosureId']}_{lang}"

            # If there's more than one language, update the messageUrl to reflect the correct language
            if len(languages) > 1:
                new_item['messageUrl'] = item['messageUrl'].replace(item['language'], lang)
            new_item['language'] = lang  # Update the language of the news item

            processed_items.append(new_item)

    # Group the processed items
    grouped_news = {}
    for item in processed_items:
        key = (item['company'], item['releaseTime'])
        if key not in grouped_news:
            grouped_news[key] = []
        grouped_news[key].append(item)

    link_related_news(grouped_news)


def link_related_news(grouped_news):
    linked_news = {}
    
    for key, items in grouped_news.items():
        # Extract numeric sequences from each disclosureId and check if they are all the same
        numeric_ids = set(re.search(r'\d+', item['disclosureId']).group() for item in items)
        # if len(items) <= 2:
        if len(items) <= 2 or len(numeric_ids) == 1:
            # Directly link items if there are 2 or fewer in the group or if the disclosureId is the same
            # logging.info(f"key={key} items={items}")
            linked_news[key] = {'relatedId': str(uuid4()), 'items': items}
        else:
            # ei toimi vielä
            logging.info(f"key={key} items={items}")
            continue
            # Attempt to group by manager names for items with more than 2 in the group.
            manager_groups = {}
            items_without_manager_name = []
            
            for item in items:
                manager_name = extract_manager_name(item['headline'])
                if manager_name:
                    print('LINK RELATED NEWS ENSIMMÄISEN IFIN ENSIMMÄINEN IF', items)
                    manager_key = (manager_name,)
                    if manager_key not in manager_groups:
                        manager_groups[manager_key] = []
                    manager_groups[manager_key].append(item)
                else:
                    print('LINK RELATED NEWS ENSIMMÄISEN IFIN TOINEN ELSE', items)
                    print(item)
                    items_without_manager_name.append(item)

            for manager_key, manager_items in manager_groups.items():
                languages = set(item['language'] for item in manager_items)
                if len(languages) == 1:
                    # If all items are of the same language, assign each a unique group ID.
                    for item in manager_items:
                        unique_key = key + manager_key + (str(uuid4()),)  # Generate unique key for each item.
                        linked_news[unique_key] = {'relatedId': str(uuid4()), 'items': [item]}
                elif len(manager_items) <= 2:
                    # If there are 2 or fewer items, link them without further analysis.
                    linked_manager_key = key + manager_key + ('LinkedByManager',)
                    linked_news[linked_manager_key] = {'relatedId': str(uuid4()), 'items': manager_items}
                else:
                    # If items vary by language and there are more than 2, consider deeper analysis or alternative handling.
                    for item in manager_items:
                        print('Multiple languages or items for manager, consider deeper analysis:', manager_key)
                        # Placeholder for deeper analysis or other logic.

            # Handle items without a manager name.
            for item in items_without_manager_name:
                print('LINK RELATED NEWS ENSIMMÄISEN ELSEN KOLMAS FOR LOOPPI', items_without_manager_name)
                # Assign a unique group ID to each ungroupable item.
                unique_key = key + ('NoManagerName', str(uuid4()))
                linked_news[unique_key] = {'relatedId': str(uuid4()), 'items': [item]}
    
    process_and_save_news(linked_news)


def last_market_close(current_time):
    # Define market hours using the correct time constructor
    market_open_time = datetime.time(9, 0)
    market_close_time = datetime.time(17, 30)

    # Handling weekday mornings before the market opens
    if current_time.weekday() < 5 and current_time.time() < market_open_time:
        # Adjust to the previous day
        adjusted_day = current_time - datetime.timedelta(days=1)
        # If the adjusted day is Sunday, keep moving back until Friday
        while adjusted_day.weekday() > 4:
            adjusted_day -= datetime.timedelta(days=1)
        return datetime.datetime.combine(adjusted_day.date(), market_close_time)

    # Handling weekday evenings after the market closes
    elif current_time.weekday() < 5 and current_time.time() > market_close_time:
        return datetime.datetime.combine(current_time.date(), market_close_time)

    # Handling weekends
    elif current_time.weekday() >= 5:
        # Calculate how many days to subtract to get back to Friday
        days_back = current_time.weekday() - 4
        last_friday = current_time - datetime.timedelta(days=days_back)
        return datetime.datetime.combine(last_friday.date(), market_close_time)

    # During market hours
    else:
        return datetime.datetime.combine(current_time.date(), market_close_time)



def fetch_stock_price_and_analyze(news_item):
    # # Create a unique cache key based on company name and release time
    # cache_key = (news_item['company'], news_item['releaseTime'])

    # # Check if data is in cache
    # if cache_key in price_cache:
    #     logging.info(f"Cache hit: Using cached data for {cache_key}")
    #     stock_info = price_cache[cache_key]
    # else:
    #     logging.info(f"Cache miss: No cached data for {cache_key}. Fetching new data.")
    #     try:
    #         # Fetch stock price from YahooFinanceApicall.py
    #         stock_info = fetch_stock_data(news_item)
    #         if stock_info:
    #             price_cache[cache_key] = stock_info  # Cache the fetched data
    #             logging.info(f"New data cached for {cache_key}")
    #         else:
    #             logging.error(f"No data fetched for {news_item['stock_symbol']}.")
    #             return
    #     except Exception as e:
    #             logging.info(f"Error fetching stock data: {e} for {news_item.get('stock_symbol')}")
    #             return

    stock_info = fetch_stock_data(news_item)

    # Save news item in MongoDB
    try:
        db.news.insert_one(news_item)
    except Exception as e:
        logging.error(f"Error inserting news item into database: {e}")
        return  # Exit the function if the news item insert fails
    
    # Get analysis from the news with the stock price from openAiApiCall.py
    # analysis_content, prompt, model_used = analyze_news(news_item, stock_info)
    try:        
        # if os.environ.get('FLASK_ENV') != 'production':
        news_narrative = news_item['messageUrlContent']
        try:
            if stock_info['is_market_hours'] == False:
                release_datetime = datetime.datetime.strptime(news_item['releaseTime'], '%Y-%m-%d %H:%M:%S')
                last_close = last_market_close(release_datetime)
                
                off_market_news_query = {
                    "stock_id": news_item['stock_id'],
                    "releaseTime": {"$gte": last_close.strftime('%Y-%m-%d %H:%M:%S'), "$lt": news_item['releaseTime']}
                }
            
                # Fetch news items
                try:
                    off_market_news = [(item['releaseTime'], item['messageUrlContent']) for item in db.news.find(off_market_news_query)]
                    off_market_news.append((news_item['releaseTime'], news_item['messageUrlContent']))
                    
                    # Sort the news items by releaseTime
                    off_market_news_sorted = sorted(off_market_news, key=lambda x: x[0])

                    # Create a narrative string from sorted news items
                    news_narrative = "\n\n".join([f"{time}: {content}" for time, content in off_market_news_sorted])
                except Exception as e:
                    logging.error(f"Error processing off-market news: {e}")
        except Exception as e:
            logging.error(f"Error with off-market news preparation: {e}")
            
            
        analysis_content, analysis_content_fi, news_and_stock_data, stock_price_forecast, model_used, returned_thread_id = analyze_news(news_narrative, stock_info, news_item['thread_id'])
        analysis_document = {
            "news_id": news_item["_id"],
            "company": news_item['company'],
            "stock_symbol": stock_info.get('symbol', None),
            "analysis_content": analysis_content,
            "analysis_content_fi": analysis_content_fi,
            "stock_price_forecast": stock_price_forecast,
            "created_at": datetime.datetime.now(pytz.timezone('Europe/Stockholm')).strftime('%Y-%m-%d %H:%M:%S'),
            "news_release_time": news_item['releaseTime'],
            "news_and_stock_data": news_and_stock_data,
            "model_used": model_used,
            "prices": [
            {
            "type": "price_before_news",
            "value": stock_info.get('price_before_news', None)
            }
        ]
        }
        
        existing_stock = db.stocks.find_one({"_id": news_item['stock_id']})
        existing_thread_id = existing_stock.get('thread_id') if existing_stock else None
        
            # Log the current thread_id before updating
        if existing_thread_id:
            logging.info(f"Current thread_id for stock_id {news_item['stock_id']}: {existing_thread_id}")
        else:
            logging.info(f"No existing thread_id for stock_id {news_item['stock_id']}")
        
        
        logging.info(f"Updating/upserting thread_id for stock_id: {news_item['stock_id']} with thread_id: {returned_thread_id}")
        # Update the stock document with the new or existing session_id
        result = db.stocks.update_one(
        {"_id": news_item['stock_id']},  # Ensure this uses the correct identifier
        {"$set": {"thread_id": returned_thread_id}},
        upsert=True  # This ensures that if the stock does not exist, it will create a new document
        )
        
        if result.matched_count > 0:
            logging.info(f"Updated thread_id for stock_id: {news_item['stock_id']}")
        if result.upserted_id:
            logging.info(f"Created new stock document with _id: {result.upserted_id}")
            
        db.analysis.insert_one(analysis_document)
        
    except Exception as e:
        logging.error(f"Error inserting analysis item into database: {e}")
        return

    # Publish a notification to Redis
    try:
        redis_client.publish('news_channel', 'New data available')
    except Exception as e:
        logging.error(f"Error publishing to Redis: {e}")
        return
    
    logging.info(f"Saved news and analysis for {news_item.get('stock_symbol')}")
    logging.info('-----------------------------NEXT NEWS ITEM----------------------------------------')

def process_and_save_news(linked_news):
    for key, value in linked_news.items():
        related_id = value['relatedId']
        for item in value['items']:
            item['relatedId'] = related_id
            unique_id = item['disclosureId']
            
            # Check for language, market, and CNS category requirements
            
            # Determine allowed markets and languages based on the environment
            if os.environ.get('FLASK_ENV') != 'production':
                # Development environment: allow both Finnish and Swedish markets
                allowed_markets = ["Main Market, Helsinki", "First North Finland", "Main Market, Stockholm", "First North Sweden"]
                allowed_languages = ['fi', 'sv']
            else:
                # Production environment: only allow Finnish markets
                allowed_markets = ["Main Market, Helsinki", "First North Finland"]
                allowed_languages = ['fi']
            
            # allowed_markets = ["Main Market, Helsinki", "First North Finland", "Main Market, Stockholm", "First North Sweden"]
            
            # if item['language'] != 'fi':
            # if item['language'] not in ['fi', 'sv']:
            #     logging.info(f"Skipping news item with ID {unique_id} due to language mismatch. Language: {item['language']}")
            #     continue
            if item['language'] not in allowed_languages:
                logging.info(f"Skipping news item with ID {unique_id} due to language mismatch. Language: {item['language']}")
                continue
            # elif item['market'] not in ["Main Market, Helsinki", "First North Finland"]:
            #     logging.info(f"Skipping news item with ID {unique_id} due to market mismatch. Market: {item['market']}")
            #     continue
            elif item['market'] not in allowed_markets:
                logging.info(f"Skipping news item with ID {unique_id} due to market mismatch. Market: {item['market']}")
                continue
            elif item['cnsCategory'] in ['Managers\' transactions', 'Managers\' Transactions', 'Changes in company\'s own shares', 'Financial Calendar']:
                logging.info(f"Skipping news item with ID {unique_id} due to CNS category mismatch. Category: {item['cnsCategory']}")
                continue
            elif any(keyword in item['headline'].lower() for keyword in ['share repurchase', 'omien osakkeiden hankinta']):
                logging.info(f"Skipping news item with ID {unique_id} due to headline content. Headline: {item['headline']}")
                continue

            
            # Check for existing item in both news and unmatched_news collections
            existing_news_item = db.news.find_one({'disclosureId': unique_id})
            existing_unmatched_item = db.unmatched_news.find_one({'disclosureId': unique_id})
            logging.info(f"Checking for existing item with ID {unique_id}: Found in news - {existing_news_item is not None}, Found in unmatched_news - {existing_unmatched_item is not None}")

            if not existing_news_item and not existing_unmatched_item:
                item_text = fetch_text_from_url(item['messageUrl'])
                if item_text:
                    item['messageUrlContent'] = item_text

                # Directly look up the stock in the database using the company name, market, and aliases
                # stock = db.stocks.find_one({"$or": [{"name": item.get('company')}, {"aliases": item.get('company')}], "market": item.get('market')})
                stocks = db.stocks.find({"$or": [{"name": item.get('company')}, {"aliases": item.get('company')}], "market": item.get('market')})
                matched = False
                # Check if any stocks were found
                
                for stock in stocks:
                    matched = True
                    # Create a copy of the item for each stock
                    stock_specific_item = item.copy()
                    
                    # Add the unique identifiers for this specific stock
                    stock_specific_item['stock_id'] = stock['_id']
                    stock_specific_item['stock_symbol'] = stock.get('symbol', 'N/A')  # Add the stock symbol to the news item
                    logging.info(f"Matched '{item.get('company')}' with stock '{stock['name']}'")
                    
                    # Check for existing openai thread_id session ID
                    if 'thread_id' in stock:
                        stock_specific_item['thread_id'] = stock['thread_id']
                    else:
                        stock_specific_item['thread_id'] = ''  # Set as empty if no thread_id is found
                    
                    # Function to fetch stock prices and analyze the news item
                    fetch_stock_price_and_analyze(stock_specific_item)

                if not matched:
                    logging.info(f"Could not find a match for news item company name '{item.get('company')}' in market '{item.get('market')}'; saved for manual review.")
                    item['review_needed'] = True
                    db.unmatched_news.insert_one(item)
                
            elif existing_news_item or existing_unmatched_item:
                logging.info(f"News item with disclosureId '{unique_id}' already exists in the database. Company '{item.get('company')}'")



def fetch_text_from_url(url):
    # Sends a GET request to the news URL and return the text content as one big string
    try:
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            text_elements = soup.find_all('p')
            all_text = " ".join(element.get_text(strip=True) for element in text_elements)
            return all_text
        else:
            logging.info("Failed to retrieve the webpage")
            return None
    except Exception as e:
        logging.info(f"Error fetching page content: {e}")
        return None

def run_once():
    logging.info("Running once cronjob and sleeping 5 seconds to start fetch 5 seconds past minute.")
    time.sleep(5)
    global price_cache
    price_cache = {}  # Reset the cache at the start of each job
    fetch_news(main_market_url)
    fetch_news(first_north_url)

def market_hours_job():
    global price_cache
    price_cache = {}  # Reset the cache at the start of each job
    logging.info(f"Scheduled job during market hours at {datetime.datetime.now(pytz.timezone('Europe/Stockholm')).strftime('%Y-%m-%d %H:%M:%S')}")
    fetch_news(main_market_url)
    fetch_news(first_north_url)
    check_and_reschedule()

def off_market_hours_job():
    global price_cache
    price_cache = {}  # Reset the cache at the start of each job
    logging.info(f"Scheduled job outside market hours at {datetime.datetime.now(pytz.timezone('Europe/Stockholm')).strftime('%Y-%m-%d %H:%M:%S')}")
    fetch_news(main_market_url)
    fetch_news(first_north_url)
    check_and_reschedule()

def check_and_reschedule():
    CET = pytz.timezone('Europe/Stockholm')
    now = datetime.datetime.now(CET)
    hour = now.hour
    weekday = now.weekday()
    
    # Clear any existing schedules regardless of the time or day
    schedule.clear()

    if weekday < 5 and 7 <= hour < 18:  # During market hours
        job = schedule.every().minute.at(":05").do(market_hours_job)
        print_next_fetch_time(job)
    else:  # Outside market hours
        job = schedule.every(15).minutes.do(off_market_hours_job)
        print_next_fetch_time(job)


def print_next_fetch_time(job):
    # Get the next scheduled run time from the job
    next_run = job.next_run
    logging.info(f"Next fetch scheduled at {next_run.strftime('%Y-%m-%d %H:%M:%S')}")


main_market_url = "https://api.news.eu.nasdaq.com/news/query.action?type=json&showAttachments=true&showCnsSpecific=true&showCompany=true&countResults=false&freeText=&market=&cnscategory=&company=&fromDate=&toDate=&globalGroup=exchangeNotice&globalName=NordicMainMarkets&displayLanguage=en&language=&timeZone=CET&dateMask=yyyy-MM-dd%20HH%3Amm%3Ass&limit=20&start=0&dir=DESC"
first_north_url = "https://api.news.eu.nasdaq.com/news/query.action?type=json&showAttachments=true&showCnsSpecific=true&showCompany=true&countResults=false&freeText=&market=&cnscategory=&company=&fromDate=&toDate=&globalGroup=exchangeNotice&globalName=NordicFirstNorth&displayLanguage=en&language=&timeZone=CET&dateMask=yyyy-MM-dd%20HH%3Amm%3Ass&limit=20&start=0&dir=DESC"


if __name__ == "__main__":
    env = os.getenv('FLASK_ENV', 'development')
    client = get_mongo_client()
    try:
        # Attempt to get the default database and log the success
        db = client.get_default_database()
        logging.info(f"Default database selected: {db.name}")
    except Exception as e:
        logging.error(f"Error getting default database: {e}")
    if env == 'production':
        logging.basicConfig(level=logging.INFO, format='%(asctime)s:%(levelname)s:%(message)s')
        run_once()  # In production, just run once when executed by cron
    else:
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s:%(levelname)s:%(message)s')
        check_and_reschedule()  # In development, use internal scheduler for frequent testing
        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            logging.info("Stopped by user.")

