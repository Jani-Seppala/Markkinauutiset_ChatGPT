import yfinance as yf
# import pandas as pd
import logging
from datetime import datetime, timedelta
import pytz
from requests import Session
from requests_cache import CacheMixin, SQLiteCache
from requests_ratelimiter import LimiterMixin, MemoryQueueBucket
from pyrate_limiter import Duration, RequestRate, Limiter


timezone = pytz.timezone('Europe/Stockholm')
class CachedLimiterSession(CacheMixin, LimiterMixin, Session):
    pass

session = CachedLimiterSession(
    limiter=Limiter(RequestRate(2, Duration.SECOND * 10)),
    bucket_class=MemoryQueueBucket,
    backend=SQLiteCache("yfinance.cache")
)

# Clear the cache at the start of the script to ensure fresh API calls
session.cache.clear()

# last_fetched_times = {}

def append_market_suffix(ticker, market):
    if "Helsinki" in market or "Finland" in market:
        return ticker + '.HE'
    elif "Stockholm" in market or "Sweden" in market:
        return ticker + '.ST'
    elif "Copenhagen" in market or "Denmark" in market:
        return ticker + '.CO'
    elif "Reykjavik" in market or "Iceland" in market:
        return ticker + '.IC'
    elif "Tallinn" in market or "Estonia" in market:
        return ticker + '.TL'
    elif "Riga" in market or "Latvia" in market:
        return ticker + '.RG'
    elif "Vilnius" in market or "Lithuania" in market:
        return ticker + '.VS'

    return ticker


def fetch_price_before_news(ticker, news_time):
    logging.info(f"Fetching price for {ticker} before news time {news_time}")
    stock = yf.Ticker(ticker)
    try:
        intraday_data = stock.history(period='1d', interval='1m', start=news_time.strftime('%Y-%m-%d'), end=(news_time + timedelta(days=1)).strftime('%Y-%m-%d'))
        logging.info(f"Intraday data for {ticker}: {intraday_data}")
        time_before_news = news_time - timedelta(minutes=1)
        logging.info(f"Time before news: {time_before_news}")
        found_data = intraday_data[intraday_data.index <= time_before_news]
        logging.info(f"Found data: {found_data}")
        
        if not found_data.empty:
            last_data = found_data.iloc[-1]
            logging.info(f"Last data before news: {last_data}")
            stock_info = stock.info
            stock_info['price_before_news'] = last_data['Close']
            logging.info(f"First if stock info: {stock_info}")
            return stock_info
        else:
            # logging.info("No intraday data found, fetching previous close.")
            # stock_info = stock.info
            # # stock_info['price_before_news'] = stock.info.get('previousClose')
            # stock_info['price_before_news'] = stock.info.get('currentPrice')
            # logging.info(f"Else stock info with current price: {stock_info}")
            # return stock_info
            # logging.info("News time not in market open time, fetching previous close.")
            # stock_info = stock.info
            # if time_before_news.hour < 9:
            #     stock_info['price_before_news'] = stock.info.get('previousClose')
            #     logging.info(f"Stock info with previous close price: {stock_info}")
            # else:
            #     current_price = stock.info.get('currentPrice')
            #     if current_price is not None:
            #         stock_info['price_before_news'] = current_price
            #         logging.info(f"Stock info with current price: {stock_info}")
            #     else:
            #         stock_info['price_before_news'] = stock.info.get('previousClose')
            #         logging.info(f"Current price not available. Stock info with previous close price: {stock_info}")
            # return stock_info
                        # Timezone for Stockholm
            # Timezone for Stockholm
            stockholm = pytz.timezone('Europe/Stockholm')
            current_time_stockholm = datetime.now(stockholm)
            # local_time_before_news = time_before_news.astimezone(stockholm)
            # logging.info(f"Local time before news: {local_time_before_news.strftime('%Y-%m-%d %H:%M:%S')}")
            logging.info(f"Current Stockholm time: {current_time_stockholm.strftime('%Y-%m-%d %H:%M:%S')}")
            market_start = datetime.strptime("09:00", "%H:%M").time()
            market_end = datetime.strptime("17:30", "%H:%M").time()
            # current_time = local_time_before_news.time()
            current_time = current_time_stockholm.time()
            logging.info(f"Comparing current time {current_time} with market start {market_start} and market end {market_end}")

            stock_info = stock.info
            if not (current_time >= market_start and current_time <= market_end):
                current_price = stock_info.get('currentPrice')
                if current_price is not None:
                    stock_info['price_before_news'] = current_price
                    logging.info(f"Stock info with current price: {stock_info}")
                else:
                    stock_info['price_before_news'] = stock_info.get('previousClose')
                    logging.info(f"Current price not available. Stock info with previous close price: {stock_info}")
            else:
                stock_info['price_before_news'] = stock_info.get('previousClose')
                logging.info(f"Stock info with previous close price outside market hours: {stock_info}")
            return stock_info
            
            
    except Exception as e:
        logging.error(f"Failed to fetch data for {ticker} at {news_time}: {e}")
        return None

def main(news_item):
    try:
        ticker = news_item.get('stock_symbol', '').replace(' ', '-')
        market = news_item.get('market')
        ticker = append_market_suffix(ticker, market)
        news_time_str = news_item['releaseTime']
        news_time = datetime.strptime(news_time_str, '%Y-%m-%d %H:%M:%S')
        news_time = pytz.timezone('Europe/Stockholm').localize(news_time)
        
        stock_info = fetch_price_before_news(ticker, news_time)
        logging.info(f"Stock data for {ticker}: {stock_info}")
        
        return stock_info
    except Exception as e:
        logging.warning(f"An error occurred: {str(e)}")
        return None
