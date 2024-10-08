import datetime
import yfinance as yf
import os
from time import sleep
import sys
import pandas as pd
import logging
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config2 import get_mongo_client

def fetch_stock_data(symbol, start_time, end_time=None):
    print(f"Symbol: {symbol}, Start time: {start_time}, End time: {end_time}")
    
     # Convert start and end times to timezone-aware Timestamps
    start_time = pd.to_datetime(start_time).tz_localize('Europe/Stockholm')
    end_time = pd.to_datetime(end_time).tz_localize('Europe/Stockholm') if end_time else None
    
    # If the market is Finnish, convert from Stockholm to Helsinki time ('Europe/Helsinki')
    if symbol.endswith('.HE'):
        start_time = start_time.tz_convert('Europe/Helsinki')
        end_time = end_time.tz_convert('Europe/Helsinki') if end_time else None
        closing_time = pd.to_datetime(start_time).normalize() + pd.Timedelta(hours=18, minutes=30)
        print(f"Adjusted times for Helsinki: Start - {start_time}, End - {end_time}")
    else:
        closing_time = pd.to_datetime(start_time).normalize() + pd.Timedelta(hours=17, minutes=30)
        print(f"Times for Stockholm: Start - {start_time}, End - {end_time}")
    
    # Subtract one minute from start and end times to align with exact news release times
    # We check if it's not exactly the closing time to avoid going out of bounds
    if start_time != closing_time:
        start_time -= pd.Timedelta(minutes=1)
    if end_time and end_time != closing_time:
        end_time -= pd.Timedelta(minutes=1)
    
    # print(f"Subtracted times for Helsinki: Start - {start_time}, End - {end_time}")
    
    try:
        data = yf.Ticker(symbol)
    except Exception as e:
        logging.error(f"Failed to fetch data for {symbol} at {start_time}: {e}")
        return None, None, None
        
    intraday_data = data.history(period='1d', interval='1m')
    filtered_data = intraday_data.loc[start_time:end_time] if end_time else intraday_data.loc[start_time:]

    if filtered_data.empty:
        daily_data = data.history(period='1d')
        
        if not daily_data.empty:
            if end_time:
                prev_close = daily_data.loc[daily_data.index < start_time, 'Close']
                if not prev_close.empty:
                    last_price = prev_close.iloc[-1]
                else:
                    # last_price = daily_data['Close'].iloc[-1]  # Use this if no trades were made before start_time
                    last_price = data.info.get('previousClose')
                print("No intraday data available. Using last available or previous close as high, low, and close.")
                return last_price, last_price, last_price
            else:
                closing_price = daily_data['Close'].iloc[-1]
                print("Using daily closing price as high, low, and close due to lack of intraday data.")
                return closing_price, closing_price, closing_price
        else:
            print("No daily data available. Using previous close as high, low, and close.")
            last_price = data.info.get('previousClose')
            return last_price, last_price, last_price
    
    # Calculate high, low, and closing prices
    high_price = filtered_data['High'].max()
    low_price = filtered_data['Low'].min()
    closing_price = filtered_data['Close'].iloc[-1]  # Closing price is the last 'Close' value

    return closing_price, high_price, low_price

def is_market_open(time):
    # Assuming market hours are from 09:00 to 17:30, Monday to Friday
    if time.weekday() >= 5:  # 5 = Saturday, 6 = Sunday
        return False
    market_open = time.replace(hour=9, minute=0, second=0, microsecond=0)
    market_close = time.replace(hour=17, minute=30, second=0, microsecond=0)
    return market_open <= time <= market_close

def get_next_market_open_time(time):
    market_open_hour = 9
    market_open_minute = 0
    market_close_hour = 17
    market_close_minute = 30

    # Ensure time is naive datetime (no timezone)
    time = time.replace(tzinfo=None)

    market_open = time.replace(hour=market_open_hour, minute=market_open_minute, second=0, microsecond=0)
    market_close = time.replace(hour=market_close_hour, minute=market_close_minute, second=0, microsecond=0)

    if time.weekday() >= 5:
        # Weekend, next market open is next Monday
        days_until_monday = (7 - time.weekday()) % 7
        next_open_day = (time + datetime.timedelta(days=days_until_monday)).date()
    elif time >= market_close:
        # After market close today, next market open is next business day
        next_day = time + datetime.timedelta(days=1)
        while next_day.weekday() >= 5:
            next_day += datetime.timedelta(days=1)
        next_open_day = next_day.date()
    else:
        # Before market opens today
        if time < market_open:
            next_open_day = time.date()
        else:
            next_open_day = time.date()

    market_open_time = datetime.datetime.combine(next_open_day, datetime.time(hour=market_open_hour, minute=market_open_minute))
    return market_open_time

def process_analysis():
    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)
    three_days_ago = today - datetime.timedelta(days=3)

    if today.weekday() == 0:  # If today is Monday
        start_date = three_days_ago
    else:
        start_date = yesterday

    start_time = datetime.datetime.combine(start_date, datetime.time(17, 30))
    end_time = datetime.datetime.combine(today, datetime.time(17, 29))

    # Fetch analyses between start_time and end_time from your database
    analyses = fetch_analyses(start_time, end_time)
    
    # Group analyses by stock_symbol instead of company
    symbol_analyses = {}
    for analysis in analyses:
        symbol = analysis.get('stock_symbol')
        if not symbol:
            logging.error(f"Analysis with id {analysis['_id']} has no 'stock_symbol', skipping.")
            continue
        if symbol in symbol_analyses:
            symbol_analyses[symbol].append(analysis)
        else:
            symbol_analyses[symbol] = [analysis]
    
    print(f'Today analysis amount: {len(analyses)}')
    
    for symbol, analyses_list in symbol_analyses.items():
        print(symbol)
        
        # Assign 'news_release_time_dt' to all analyses before sorting
        for analysis in analyses_list:
            news_time = datetime.datetime.strptime(analysis['news_release_time'], '%Y-%m-%d %H:%M:%S')
            news_time = news_time.replace(tzinfo=None)
            analysis['news_release_time_dt'] = news_time
        
        # Now sort analyses
        sorted_analyses = sorted(analyses_list, key=lambda x: x['news_release_time_dt'])

        current_group = []
        i = 0
        while i < len(sorted_analyses):
            analysis = sorted_analyses[i]
            news_time = analysis['news_release_time_dt']

            if is_market_open(news_time):
                if current_group:
                    # Process the off-market group
                    first_analysis = current_group[0]
                    group_start_time = get_next_market_open_time(first_analysis['news_release_time_dt'])
                    group_end_time = news_time - datetime.timedelta(minutes=1)
                    # Fetch data from group_start_time to group_end_time
                    closing_price, high_price, low_price = fetch_stock_data(symbol, group_start_time, group_end_time)
                    # Update prices for each analysis in current_group
                    for group_analysis in current_group:
                        print(f'Updating analysis id: {group_analysis["_id"]} with prices: {closing_price}, {high_price}, {low_price}')
                        update_database_with_prices(group_analysis['_id'], closing_price, high_price, low_price)
                        sleep(15)
                    current_group = []
                # Now process the current in-market analysis individually
                next_analysis_time = None
                if i + 1 < len(sorted_analyses):
                    next_analysis_time = sorted_analyses[i+1]['news_release_time_dt'] - datetime.timedelta(minutes=1)
                closing_price, high_price, low_price = fetch_stock_data(symbol, news_time, next_analysis_time)
                print(f'Updating analysis id: {analysis["_id"]} with prices: {closing_price}, {high_price}, {low_price}')
                update_database_with_prices(analysis['_id'], closing_price, high_price, low_price)
                sleep(15)
            else:
                current_group.append(analysis)
            i += 1

        # After the loop, if current_group is not empty, process it
        if current_group:
            # Process the off-market group
            first_analysis = current_group[0]
            group_start_time = get_next_market_open_time(first_analysis['news_release_time_dt'])
            # Since there is no in-market analysis after, set group_end_time to market close
            group_end_time = group_start_time.replace(hour=17, minute=30)
            closing_price, high_price, low_price = fetch_stock_data(symbol, group_start_time, group_end_time)
            # Update prices for each analysis in current_group
            for group_analysis in current_group:
                print(f'Updating analysis id: {group_analysis["_id"]} with prices: {closing_price}, {high_price}, {low_price}')
                update_database_with_prices(group_analysis['_id'], closing_price, high_price, low_price)
                sleep(15)


def fetch_analyses(start_time, end_time):    
    start_time_str = start_time.strftime('%Y-%m-%d %H:%M:%S')
    end_time_str = end_time.strftime('%Y-%m-%d %H:%M:%S')
    
    # Fetch news items within the time range
    analyses = db['analysis'].find({
        "news_release_time": {
            "$gte": start_time_str,
            "$lt": end_time_str
        }
    })
    
    analysis_list = list(analyses)
    print('-----------------------------------')
    return analysis_list

def update_database_with_prices(analysis_id, closing_price, high_price, low_price):
    
    update_document = {
        "$push": {
            "prices": {
                "$each": [
                    {"type": "closing_price", "value": closing_price},
                    {"type": "high_price", "value": high_price},
                    {"type": "low_price", "value": low_price}
                ]
            }
        }
    }
    
    try:
        result = db['analysis'].update_one({"_id": analysis_id}, update_document)
        if result.matched_count > 0:
            logging.info(f"Successfully updated analysis ID {analysis_id} with new price data.")
        else:
            logging.warning(f"No matching document found with ID {analysis_id}.")
    except Exception as e:
        logging.error(f"Failed to update analysis ID {analysis_id}: {e}")
        

if __name__ == "__main__":
    client = get_mongo_client()
    try:
        # Attempt to get the default database and log the success
        db = client.get_default_database()
        logging.info(f"Default database selected: {db.name}")
    except Exception as e:
        logging.error(f"Error getting default database: {e}")
    else:
        try:
            process_analysis()
        except Exception as e:
            logging.error(f"Error processing analysis: {e}")
