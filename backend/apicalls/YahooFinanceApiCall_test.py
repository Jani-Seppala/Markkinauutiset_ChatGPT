import yfinance as yf
import pandas as pd
import logging
from datetime import datetime, timedelta
import pytz
from app import mongo
from requests import Session
from requests_cache import CacheMixin, SQLiteCache
from requests_ratelimiter import LimiterMixin, MemoryQueueBucket
from pyrate_limiter import Duration, RequestRate, Limiter
# from pymongo import MongoClient, ASCENDING

# Set up the database and session
news_collection = mongo.db.news

timezone = pytz.timezone('Europe/Stockholm')
class CachedLimiterSession(CacheMixin, LimiterMixin, Session):
    pass

session = CachedLimiterSession(
    limiter=Limiter(RequestRate(2, Duration.SECOND * 5)),
    bucket_class=MemoryQueueBucket,
    backend=SQLiteCache("yfinance.cache")
)

# Clear the cache at the start of the script to ensure fresh API calls
session.cache.clear()

last_fetched_times = {}

def append_market_suffix(ticker, market):
    if "Helsinki" in market or "Finland" in market:
        return ticker + '.HE'
    elif "Stockholm" in market or "Sweden" in market:
        return ticker + '.ST'
    elif "Copenhagen" in market or "Denmark" in market:
        return ticker + '.CO'
    elif "Reykjavik" in market or "Iceland" in market:
        return ticker + '.IC'
    return ticker


def fetch_and_process_intraday_data(ticker, news_time):
    stock = yf.Ticker(ticker, session=session)
    try:
        # Attempt to fetch intraday data on the news date
        intraday_data = stock.history(period='1d', interval='1m', start=news_time.strftime('%Y-%m-%d'), end=(news_time + timedelta(days=1)).strftime('%Y-%m-%d'))
        time_before_news = news_time - timedelta(minutes=1)
        # Search for price data just before the news release
        for date, data in reversed(list(intraday_data.iterrows())):
            if date <= time_before_news:
                return data['Close'], date  # Return the found price and its timestamp
    except Exception as e:
        print(f"Error fetching intraday data for {ticker}: {e}")

    # Fallback to the last available close price if no intraday data is available
    previous_close = stock.info.get('previousClose')
    previous_close_date = news_time - timedelta(days=1)  # Assume the previous close date is the day before
    print(f"No intraday data available for {ticker} as of {news_time}, using previous close: {previous_close}")
    return previous_close, previous_close_date



def process_historical_data(ticker, news_time):
    stock = yf.Ticker(ticker, session=session)
    # Ensure the coverage of a year's data based on the news time
    start_date = (news_time - timedelta(days=365)).strftime('%Y-%m-%d')
    end_date = news_time.strftime('%Y-%m-%d')
    hist = stock.history(start=start_date, end=end_date, interval='1d')

    # Debugging prints
    # print(f"Fetched historical data from {start_date} to {end_date} for {ticker}")
    # print("Historical data head:", hist.head())
    # print("Historical data tail:", hist.tail())

    target_dates = {
        'yesterday': news_time - timedelta(days=1),
        '1_week_ago': news_time - timedelta(weeks=1),
        '1_month_ago': news_time - timedelta(days=30),
        '1_year_ago': news_time - timedelta(days=365)
    }
    close_prices = {}

    for label, target_date in target_dates.items():
        # Normalize the target date for comparison
        target_date_norm = pd.to_datetime(target_date).normalize()
        # print(f"Checking for {label} on {target_date_norm}")

        # Filtering the dataframe for the target date
        filtered_data = hist[hist.index.normalize() == target_date_norm]
        if not filtered_data.empty:
            close_price = filtered_data['Close'].iloc[0]
            close_prices[label] = close_price
            # print(f"Matched {label}: {close_price} on {filtered_data.index[0]}")
        else:
            # print(f"No match found for {label}. Looking for closest date before {target_date_norm}")
            # Find the closest date before the target date
            prior_dates = hist[hist.index < target_date_norm]
            if not prior_dates.empty:
                closest_date = prior_dates.index.max()
                closest_price = prior_dates.loc[closest_date, 'Close']
                close_prices[label] = closest_price
                # print(f"Closest match for {label}: {closest_price} on {closest_date}")
            else:
                close_prices[label] = None
                # print(f"No historical data available before {target_date_norm} for {label}")

    return close_prices


def main():
    for news_item in news_collection.find():
        ticker = news_item.get('stock_symbol', '').replace(' ', '-')
        market = news_item.get('market')
        ticker = append_market_suffix(ticker, market)
        news_time_str = news_item['releaseTime']
        news_time = datetime.strptime(news_time_str, '%Y-%m-%d %H:%M:%S')
        news_time = timezone.localize(news_time)

        if ticker not in last_fetched_times or (news_time - last_fetched_times.get(ticker, datetime.min.replace(tzinfo=timezone)) > timedelta(minutes=900)):
            price_before_news, time_of_price = fetch_and_process_intraday_data(ticker, news_time)
            close_prices = process_historical_data(ticker, news_time)  # Adjusted to use news_time instead of now
            print(f"Data fetched for {ticker}: Price before news {price_before_news} at {time_of_price}, Historical prices: {close_prices}")
            last_fetched_times[ticker] = news_time
        else:
            print(f"Skipping data fetch for {ticker} due to recent fetch at {last_fetched_times[ticker]}.")

        print('--------------------------------------------------------------')


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"An error occurred: {str(e)}")
