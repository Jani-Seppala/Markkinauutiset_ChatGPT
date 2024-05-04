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
    stock = yf.Ticker(ticker)
    try:
        intraday_data = stock.history(period='1d', interval='1m', start=news_time.strftime('%Y-%m-%d'), end=(news_time + timedelta(days=1)).strftime('%Y-%m-%d'))
        time_before_news = news_time - timedelta(minutes=1)
        found_data = intraday_data[intraday_data.index <= time_before_news]
        
        if not found_data.empty:
            last_data = found_data.iloc[-1]
            stock_info = stock.info
            stock_info['price_before_news'] = last_data['Close']
            return stock_info
        else:
            logging.info("No intraday data found, fetching previous close.")
            stock_info = stock.info
            # stock_info['price_before_news'] = stock.info.get('previousClose')
            stock_info['price_before_news'] = stock.info.get('currentPrice')
            return stock_info
    except Exception as e:
        logging.warning(f"Failed to fetch data for {ticker} at {news_time}: {e}")
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
