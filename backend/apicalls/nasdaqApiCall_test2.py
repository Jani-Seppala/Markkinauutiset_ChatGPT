import requests
from bs4 import BeautifulSoup
from app import mongo
from fuzzywuzzy import process
import re

print('fsfs')

def fetch_news():
    mainMarketUrl = "https://api.news.eu.nasdaq.com/news/query.action?type=json&showAttachments=true&showCnsSpecific=true&showCompany=true&countResults=false&freeText=&market=&cnscategory=&company=&fromDate=&toDate=&globalGroup=exchangeNotice&globalName=NordicMainMarkets&displayLanguage=fi&language=&timeZone=CET&dateMask=yyyy-MM-dd%20HH%3Amm%3Ass&limit=20&start=0&dir=DESC"
    # mainMarketUrlEn = "https://api.news.eu.nasdaq.com/news/query.action?type=json&showAttachments=true&showCnsSpecific=true&showCompany=true&countResults=false&freeText=&market=&cnscategory=&company=&fromDate=&toDate=&globalGroup=exchangeNotice&globalName=NordicMainMarkets&displayLanguage=en&language=&timeZone=CET&dateMask=yyyy-MM-dd%20HH%3Amm%3Ass&limit=20&start=0&dir=DESC"
    # firstNorthUrl = "https://api.news.eu.nasdaq.com/news/query.action?type=json&showAttachments=true&showCnsSpecific=true&showCompany=true&countResults=false&freeText=&market=&cnscategory=&company=&fromDate=&toDate=&globalGroup=exchangeNotice&globalName=NordicFirstNorth&displayLanguage=fi&language=&timeZone=CET&dateMask=yyyy-MM-dd%20HH%3Amm%3Ass&limit=20&start=0&dir=DESC"
    response = requests.get(mainMarketUrl)
    if response.status_code == 200:
        news_data = response.json()
        process_and_save_news(news_data)
    else:
        print(f"Failed to fetch news: {response.status_code}")


def normalize_company_name(name):
    name = re.sub(r'[\s.,;:\'\"()&/]+', '', name).lower()
    for suffix in ['ab', 'oyj', 'plc', 'as', 'ltd']:
        if name.endswith(suffix):
            name = name[:-len(suffix)]
    return name

def find_best_stock_match(company_name, stocks_collection):
    normalized_company_name = normalize_company_name(company_name)
    stock_names = {stock['_id']: normalize_company_name(stock['name']) for stock in stocks_collection}
    best_match, score = process.extractOne(normalized_company_name, stock_names.values())
    
    if score > 85:  # You may adjust this threshold based on your observation
        stock_id = list(stock_names.keys())[list(stock_names.values()).index(best_match)]
        return stock_id
    else:
        return None

def process_and_save_news(news_data):
    stocks_collection = list(mongo.db.stocks.find({}))  # Fetch all stocks once to improve efficiency
    for item in news_data['results']['item']:
        unique_id = item['disclosureId']
        existing_news_item = mongo.db.news.find_one({'disclosureId': unique_id})
        
        if not existing_news_item:
            item_text = fetch_text_from_url(item['messageUrl'])
            if item_text:
                item['messageUrlContent'] = item_text

            # Filter stocks by market and attempt to find the best matching stock
            stock_id = find_best_stock_match(item.get('company'), stocks_collection)
            if stock_id:
                item['stock_id'] = stock_id
                
                # Debug print to check match result
                matched_stock_name = next((stock['name'] for stock in stocks_collection if stock['_id'] == stock_id), None)
                print(f"Matched '{item.get('company')}' with stock '{matched_stock_name}'")
                
                mongo.db.news.insert_one(item)
                # print(item)
            else:
                print(f"Could not find a good match for news item company name '{item.get('company')}'.")


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
            print("Failed to retrieve the webpage")
            return None
    except Exception as e:
        print(f"Error fetching page content: {e}")
        return None


fetch_news()


# import requests
# from bs4 import BeautifulSoup
# # from app import mongo  # Comment this out if you're just printing to console for now
# import re
# from fuzzywuzzy import process  # Ensure you have fuzzywuzzy installed

# print('Fetching news...')

# def fetch_news():
#     mainMarketUrl = "https://api.news.eu.nasdaq.com/news/query.action?type=json&showAttachments=true&showCnsSpecific=true&showCompany=true&countResults=false&freeText=&market=&cnscategory=&company=&fromDate=&toDate=&globalGroup=exchangeNotice&globalName=NordicMainMarkets&displayLanguage=fi&language=&timeZone=CET&dateMask=yyyy-MM-dd%20HH%3Amm%3Ass&limit=20&start=0&dir=DESC"
#     # firstNorthUrl = "https://api.news.eu.nasdaq.com/news/query.action?type=json&showAttachments=true&showCnsSpecific=true&showCompany=true&countResults=false&freeText=&market=&cnscategory=&company=&fromDate=&toDate=&globalGroup=exchangeNotice&globalName=NordicFirstNorth&displayLanguage=fi&language=&timeZone=CET&dateMask=yyyy-MM-dd%20HH%3Amm%3Ass&limit=20&start=0&dir=DESC"
#     response = requests.get(mainMarketUrl)
#     if response.status_code == 200:
#         news_data = response.json()
#         process_and_save_news(news_data)
#     else:
#         print(f"Failed to fetch news: {response.status_code}")

# def normalize_name(name):
#     name = re.sub(r'[\s.,;:\'\"()&/]+', '', name).lower()
#     for suffix in ['ab', 'oyj', 'plc', 'as', 'ltd']:
#         if name.endswith(suffix):
#             name = name[:-len(suffix)]
#     return name

# def find_best_stock_match(company_name, stocks_collection):
#     normalized_company_name = normalize_name(company_name)
#     stock_names = {stock['_id']: normalize_name(stock['name']) for stock in stocks_collection}
#     best_match, score = process.extractOne(normalized_company_name, stock_names.values())
    
#     if score > 85:
#         stock_id = list(stock_names.keys())[list(stock_names.values()).index(best_match)]
#         return stock_id
#     else:
#         return None

# def process_and_save_news(news_data):
#     for item in news_data['results']['item']:
#         market = item.get('market')
#         unique_id = item['disclosureId']

#         # For testing, simulate finding an existing news item as None
#         existing_news_item = None  # mongo.db.news.find_one({'disclosureId': unique_id})
        
#         if not existing_news_item:
#             item_text = fetch_text_from_url(item['messageUrl'])
#             if item_text:
#                 item['messageUrlContent'] = item_text

#             stocks_in_market = [{"_id": "mock_id", "name": item.get('company'), "market": market}]  # Mock data for testing
#             stock_id = find_best_stock_match(item.get('company'), stocks_in_market)
#             if stock_id:
#                 item['stock_id'] = stock_id
#                 print(f"Prepared news item for MongoDB insertion: {item}")  # Print instead of insert
#                 # mongo.db.news.insert_one(item)  # Commented out for testing
#             else:
#                 print(f"Could not find a good match for news item company name '{item.get('company')}' in market '{market}'.")

# def fetch_text_from_url(url):
#     try:
#         response = requests.get(url)
#         if response.status_code == 200:
#             soup = BeautifulSoup(response.text, 'html.parser')
#             text_elements = soup.find_all('p')
#             all_text = " ".join(element.get_text(strip=True) for element in text_elements)
#             return all_text
#         else:
#             print("Failed to retrieve the webpage")
#             return None
#     except Exception as e:
#         print(f"Error fetching page content: {e}")
#         return None

# fetch_news()
