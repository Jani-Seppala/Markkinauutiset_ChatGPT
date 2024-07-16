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
# import redis

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
        if len(items) <= 2:
            # print('LINK RELATED NEWS ENSIMMÄINEN IF')
            # Directly link items if there are 2 or fewer in the group.
            # direct_link_key = key + ('DirectLink',)
            # linked_news[direct_link_key] = {'relatedId': str(uuid4()), 'items': items}
            linked_news[key] = {'relatedId': str(uuid4()), 'items': items}
        else:
            # ei toimi vielä
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


def fetch_stock_price_and_analyze(news_item):
    # Create a unique cache key based on company name and release time
    cache_key = (news_item['company'], news_item['releaseTime'])
    print(f"{price_cache=} fetch_stock_price_and_analyze eka print")

    # Check if data is in cache
    if cache_key in price_cache:
        price_before_news, close_prices = price_cache[cache_key]
        logging.info("Using cached price data.")
        logging.info(f"{price_cache=}")
    else:
        try:
            # Fetch stock price from YahooFinanceApicall.py
            # price_before_news, close_prices = fetch_stock_data(news_item)
            # Store in cache
            # price_cache[cache_key] = (price_before_news, close_prices)
            stock_info = fetch_stock_data(news_item)
                # Store in cache
            price_cache[cache_key] = stock_info
            logging.info("Fetched new price data and cached it.")
        except Exception as e:
                logging.info(f"Error fetching stock data: {e} for {news_item.get('stock_symbol')}")
                return
            
    
    if 'price_before_news' in stock_info:
        news_item['price_before_news'] = stock_info['price_before_news']
    else:
        logging.info("Price before news not found in stock info.")
        return

    # Save news item in MongoDB
    try:
        db.news.insert_one(news_item)
    except Exception as e:
        logging.error(f"Error inserting news item into database: {e}")
        return  # Exit the function if the news item insert fails
    
    # Get analysis from the news with the stock price from openAiApiCall.py
    # analysis_content, prompt, model_used = analyze_news(news_item, stock_info)
    try:
        # if os.environ.get('FLASK_ENV') == 'production':
        if os.environ.get('FLASK_ENV') != 'production':
            analysis_content, prompt, model_used = analyze_news(news_item, stock_info)
        else:
            analysis_content = "This is static analysis content for testing."
            prompt = "Static prompt for testing."
            model_used = "Static model for testing."
            
        analysis_document = {
            "news_id": news_item["_id"],
            "company": news_item['company'],
            "analysis_content": analysis_content,
            "created_at": datetime.datetime.now(pytz.timezone('Europe/Stockholm')).strftime('%Y-%m-%d %H:%M:%S'),
            "prompt": prompt,
            "model_used": model_used
        }
        
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
            
            # # Check for language and market requirements
            # if item['language'] != 'fi' or (item['market'] not in ["Main Market, Helsinki", "First North Finland"]):
            #     logging.info(f"Skipping news item with ID {unique_id} due to language/market mismatch.")
            #     continue
            
            # # Check for language, market, and CNS category requirements
            # if (item['language'] != 'fi' 
            #     or item['market'] not in ["Main Market, Helsinki", "First North Finland"]
            #     or item['cnsCategory'] in ['Managers\' transactions', 'Managers\' Transactions', 'Changes in company\'s own shares']):
            #     logging.info(f"Skipping news item with ID {unique_id} and cnsCategory {item['cnsCategory']} due to language/market/CNS category mismatch.")
            #     continue
            
            # Check for language, market, and CNS category requirements
            if item['language'] != 'fi':
                logging.info(f"Skipping news item with ID {unique_id} due to language mismatch. Language: {item['language']}")
                continue
            elif item['market'] not in ["Main Market, Helsinki", "First North Finland"]:
                logging.info(f"Skipping news item with ID {unique_id} due to market mismatch. Market: {item['market']}")
                continue
            elif item['cnsCategory'] in ['Managers\' transactions', 'Managers\' Transactions', 'Changes in company\'s own shares']:
                logging.info(f"Skipping news item with ID {unique_id} due to CNS category mismatch. Category: {item['cnsCategory']}")
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
                stock = db.stocks.find_one({"$or": [{"name": item.get('company')}, {"aliases": item.get('company')}], "market": item.get('market')})
                if stock:
                    item['stock_id'] = stock['_id']
                    item['stock_symbol'] = stock.get('symbol', 'N/A')  # Add the stock symbol to the news item
                    logging.info(f"Matched '{item.get('company')}' with stock '{stock['name']}'")
                    fetch_stock_price_and_analyze(item)
                else:
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
        # job = schedule.every(15).minutes.do(off_market_hours_job)
        job = schedule.every(2).minutes.do(off_market_hours_job)
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

