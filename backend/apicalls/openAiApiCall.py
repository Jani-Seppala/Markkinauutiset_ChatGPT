from openai import OpenAI
import tiktoken
import os
import logging
import time
import sys
import json

client = OpenAI()

def analyze_news(news_item, stock_info, thread_id=None):
    """Generates an analysis for a given news item and associated stock price data."""
    
    start_time = time.time()
    try:

        news_and_stock_data = f"Latest stock news: {news_item}, Latest stock data: {stock_info}"
        thread = None
        model_used = None
        if not thread_id:
            # Create a new thread if no thread_id is present
            thread = client.beta.threads.create()
            thread_id = thread.id


        client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=news_and_stock_data
        )

        if os.environ.get('FLASK_ENV') != 'production':
            assistant_id="asst_0DkQjeTlGeZ6CU5YQ8B2DDwa"
            model_used = "gpt-4o-mini"
        else:
            assistant_id="asst_YERuuoYl1prF5Mm8qSoPVPyb"
            model_used = "gpt-4o"

        run = client.beta.threads.runs.create_and_poll(
            thread_id=thread_id,
            assistant_id=assistant_id
        )
        
        if run.status == 'completed':
            messages = client.beta.threads.messages.list(thread_id=thread_id)
            
            # logging.info(f"Messages: {messages}")
            # print(messages.data[0].content[0].text.value)
            # sys.exit()
            if messages.data:
                latest_message = messages.data[0]  # The first message in the list, since sorted by 'desc'
                if hasattr(latest_message, 'content') and isinstance(latest_message.content, list):
                    # Assume content is a list of blocks, typically you would find text blocks
                    
                    # text_blocks = [block.text.value for block in latest_message.content if block.type == 'text']
                    # analysis_content = " ".join(text_blocks)
                    # logging.info(f"Analysis content: {analysis_content}, news_and_stock_data: {news_and_stock_data}, model: {model_used}, thread_id: {thread_id}")
                    # return analysis_content, news_and_stock_data, model_used, thread_id
                    analysis_json = json.loads(latest_message.content[0].text.value)  # Assuming JSON response
                    analysis_text = analysis_json['analysis_text']
                    stock_price_forecast = analysis_json['stock_price_forecast']
                
                    full_analysis = f"{analysis_text}\n\nForecast for stock price reaction: {stock_price_forecast}"
                    
                    # print(json.dumps(analysis_json, indent=4))  # Pretty print the JSON object
                    
                    logging.info(f"Full analysis: {full_analysis}, Stock price forecast: {stock_price_forecast}, Model: {model_used}, Thread ID: {thread_id}")
                    
                    return full_analysis, news_and_stock_data, stock_price_forecast, model_used, thread_id  
                
            return "No analysis content found.", None, None, None, thread_id
        else:
            return f"Run Status: {run.status}", None, None, None, thread_id

    except Exception as e:
        elapsed_time = time.time() - start_time
        logging.error(f"An error occurred in analyze_news after {elapsed_time:.2f} seconds: {e}")
        return (f"An error occurred in analyze_news: {str(e)}", news_and_stock_data, None, None, thread_id)

