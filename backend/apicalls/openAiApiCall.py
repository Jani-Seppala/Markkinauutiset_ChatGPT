from openai import OpenAI
import tiktoken
import os
import logging
import time
import sys
import json

client = OpenAI()

# def analyze_news(news_item, stock_info, thread_id=None):
#     """Generates an analysis for a given news item and associated stock price data."""
    
#     start_time = time.time()
#     try:

#         news_and_stock_data = f"Latest stock news: {news_item}, Latest stock data: {stock_info}"
#         thread = None
#         model_used = None
#         if not thread_id:
#             # Create a new thread if no thread_id is present
#             thread = client.beta.threads.create()
#             thread_id = thread.id

#         client.beta.threads.messages.create(
#             thread_id=thread_id,
#             role="user",
#             content=news_and_stock_data
#         )

#         if os.environ.get('FLASK_ENV') != 'production':
#             assistant_id="asst_0DkQjeTlGeZ6CU5YQ8B2DDwa"
#             model_used = "gpt-4o-mini"
#         else:
#             assistant_id="asst_YERuuoYl1prF5Mm8qSoPVPyb"
#             model_used = "gpt-4o"

#         run = client.beta.threads.runs.create_and_poll(
#             thread_id=thread_id,
#             assistant_id=assistant_id
#         )
        
#         if run.status == 'completed':
#             messages = client.beta.threads.messages.list(thread_id=thread_id)
            
#             if messages.data:
#                 latest_message = messages.data[0]  # The first message in the list, since sorted by 'desc'
#                 if hasattr(latest_message, 'content') and isinstance(latest_message.content, list):
#                     analysis_json = json.loads(latest_message.content[0].text.value)  # Assuming JSON response
#                     analysis_text = analysis_json['analysis_text']
#                     stock_price_forecast = analysis_json['stock_price_forecast']
                
#                     full_analysis = f"{analysis_text}\n\nForecast for stock price reaction: {stock_price_forecast}"
                    
#                     # translated_analysis = get_translation(full_analysis, target_language='fi')
                    
#                     logging.info(f"Full analysis: {full_analysis}, Stock price forecast: {stock_price_forecast}, Model: {model_used}, Thread ID: {thread_id}")
                    
#                     # return full_analysis, news_and_stock_data, stock_price_forecast, model_used, thread_id, translated_analysis
#                     return full_analysis, news_and_stock_data, stock_price_forecast, model_used, thread_id, None
                
#             return "No analysis content found.", None, None, None, thread_id
#         else:
#             return f"Run Status: {run.status}", None, None, None, thread_id

#     except Exception as e:
#         elapsed_time = time.time() - start_time
#         logging.error(f"An error occurred in analyze_news after {elapsed_time:.2f} seconds: {e}")
#         return (f"An error occurred in analyze_news: {str(e)}", news_and_stock_data, None, None, thread_id)

    
# def get_translation(text, target_language):
#     try:
#         # Construct the prompt for translation
#         translation_prompt = f"Translate the following text to {target_language}:\n\n{text}"
        
#         assistant_id = "asst_74Daf2s1LBoCT1N5WhNApksL"
        
#         # if os.environ.get('FLASK_ENV') != 'production':
#         #     assistant_id="asst_0DkQjeTlGeZ6CU5YQ8B2DDwa"  # Use a specific assistant ID for non-production
#         #     model_used = "gpt-4o-mini"  # Simpler model for non-production
#         # else:
#         #     assistant_id="asst_YERuuoYl1prF5Mm8qSoPVPyb"  # Use a different assistant ID for production
#         #     model_used = "gpt-4o"  # More capable model for production
        
        
#         thread = client.beta.threads.create()  # First, create a thread
#         client.beta.threads.messages.create(
#             thread_id=thread.id,
#             role="user",
#             content=translation_prompt
#         )
        
#         run = client.beta.threads.runs.create_and_poll(
#             thread_id=thread.id,
#             assistant_id=assistant_id
#         )
        
#         # Checking if the run completed successfully
#         if run.status == 'completed':
#             # Fetch messages from the thread
#             messages = client.beta.threads.messages.list(thread_id=thread.id)
#             # Find the assistant's response
#             for message in messages.data:
#                 if message.role == 'assistant':
#                     return message.content  # Return the content of the assistant's message
#             return "No translation found."  # In case no assistant message is found
#         else:
#             return f"Run was not successful: {run.status}"

#     except Exception as e:
#         logging.error(f"Translation error: {e}")
#         return None


def analyze_news(news_item, stock_info, thread_id_en=None):
    """Generates analyses for a given news item and associated stock price data in both English and Finnish."""

    start_time = time.time()
    try:
        news_and_stock_data = f"Latest stock news: {news_item}, Latest stock data: {stock_info}"

        if os.environ.get('FLASK_ENV') != 'production':
            # Development environment assistant IDs
            assistant_id_en = "asst_0DkQjeTlGeZ6CU5YQ8B2DDwa"
            assistant_id_fi = "asst_74Daf2s1LBoCT1N5WhNApksL"
            model_used = "gpt-4o-mini"
        else:
            # Production environment assistant IDs
            assistant_id_en = "asst_YERuuoYl1prF5Mm8qSoPVPyb"
            assistant_id_fi = "asst_74Daf2s1LBoCT1N5WhNApksL"
            model_used = "gpt-4o"

        # Prepare the English thread
        if not thread_id_en:
            # Create a new thread if no thread_id is present
            thread_en = client.beta.threads.create()
            thread_id_en = thread_en.id
        # else:
            # Reuse existing thread
            # thread_en = client.beta.threads.get(thread_id=thread_id_en)

        client.beta.threads.messages.create(
            thread_id=thread_id_en,
            role="user",
            content=news_and_stock_data
        )

        # Create a new thread for the Finnish analysis
        thread_fi = client.beta.threads.create()
        thread_id_fi = thread_fi.id

        client.beta.threads.messages.create(
            thread_id=thread_id_fi,
            role="user",
            content=news_and_stock_data
        )

        # Start both runs without blocking

        # English run
        run_en = client.beta.threads.runs.create(
            thread_id=thread_id_en,
            assistant_id=assistant_id_en
        )

        # Finnish run
        run_fi = client.beta.threads.runs.create(
            thread_id=thread_id_fi,
            assistant_id=assistant_id_fi
        )

        # Use the helper function to poll both runs until completion
        # run_statuses = poll_runs_until_complete(client, [run_en, run_fi])
        
        runs_with_thread_ids = [
            (run_en, thread_id_en),
            (run_fi, thread_id_fi)
        ]

        # Use the helper function to poll both runs until completion
        run_statuses = poll_runs_until_complete(client, runs_with_thread_ids)

        if run_statuses[run_en.id]['status'] == 'completed':
            messages_en = client.beta.threads.messages.list(thread_id=thread_id_en)
            if messages_en.data:
                latest_message_en = messages_en.data[0]
                if hasattr(latest_message_en, 'content') and isinstance(latest_message_en.content, list):
                    assistant_response_en = latest_message_en.content[0].text.value
                    logging.debug(f"Assistant response (EN): {assistant_response_en}")
                    try:
                        analysis_json_en = json.loads(assistant_response_en)
                        analysis_text_en = analysis_json_en.get('analysis_text')
                        stock_price_forecast_en = analysis_json_en.get('stock_price_forecast')
                        if analysis_text_en and stock_price_forecast_en:
                            full_analysis_en = f"{analysis_text_en}\n\nForecast for stock price reaction: {stock_price_forecast_en}"
                        else:
                            logging.error("English assistant response is missing expected keys.")
                            full_analysis_en = stock_price_forecast_en = None
                    except json.JSONDecodeError as e:
                        logging.error(f"JSON decoding error in English analysis: {e}")
                        full_analysis_en = stock_price_forecast_en = None
                else:
                    logging.error("English assistant message content is not in the expected format.")
                    full_analysis_en = stock_price_forecast_en = None
            else:
                logging.error("No messages found in English thread.")
                full_analysis_en = stock_price_forecast_en = None
        else:
            full_analysis_en = stock_price_forecast_en = None

        # Finnish analysis
        if run_statuses[run_fi.id]['status'] == 'completed':
            messages_fi = client.beta.threads.messages.list(thread_id=thread_id_fi)
            if messages_fi.data:
                latest_message_fi = messages_fi.data[0]
                if hasattr(latest_message_fi, 'content') and isinstance(latest_message_fi.content, list):
                    assistant_response_fi = latest_message_fi.content[0].text.value
                    logging.debug(f"Assistant response (FI): {assistant_response_fi}")
                    try:
                        analysis_json_fi = json.loads(assistant_response_fi)
                        analysis_text_fi = analysis_json_fi.get('analysis_text')
                        stock_price_forecast_fi = analysis_json_fi.get('stock_price_forecast')
                        if analysis_text_fi and stock_price_forecast_fi:
                            full_analysis_fi = f"{analysis_text_fi}\n\nEnnuste osakekurssin reaktiolle: {stock_price_forecast_fi}"
                        else:
                            logging.error("Finnish assistant response is missing expected keys.")
                            full_analysis_fi = stock_price_forecast_fi = None
                    except json.JSONDecodeError as e:
                        logging.error(f"JSON decoding error in Finnish analysis: {e}")
                        full_analysis_fi = stock_price_forecast_fi = None
                else:
                    logging.error("Finnish assistant message content is not in the expected format.")
                    full_analysis_fi = stock_price_forecast_fi = None
            else:
                logging.error("No messages found in Finnish thread.")
                full_analysis_fi = stock_price_forecast_fi = None
        else:
            full_analysis_fi = stock_price_forecast_fi = None

        # Return both analyses and the thread ID for English analysis
        return full_analysis_en, full_analysis_fi, news_and_stock_data, stock_price_forecast_en, model_used, thread_id_en

    
    except Exception as e:
        elapsed_time = time.time() - start_time
        logging.error(f"An error occurred in analyze_news after {elapsed_time:.2f} seconds: {e}")
        return None, None, None, None, None, None


def poll_runs_until_complete(client, runs_with_thread_ids, max_wait_time=300, poll_interval=1):
    """
    Polls the given runs until they are completed or a timeout is reached.
    `runs_with_thread_ids` is a list of tuples (run, thread_id)
    Returns a dictionary with run IDs as keys and their statuses and results.
    """
    import time
    start_time = time.time()
    run_statuses = {run.id: {'status': 'pending', 'result': None, 'thread_id': thread_id} for run, thread_id in runs_with_thread_ids}

    while True:
        all_completed = True
        for run, thread_id in runs_with_thread_ids:
            if run_statuses[run.id]['status'] != 'completed':
                all_completed = False
                # Retrieve the run status
                run_status = client.beta.threads.runs.retrieve(
                    thread_id=thread_id,
                    run_id=run.id
                )
                run_statuses[run.id]['status'] = run_status.status
                if run_status.status == 'completed':
                    run_statuses[run.id]['result'] = run_status
        if all_completed:
            break
        if time.time() - start_time > max_wait_time:
            raise TimeoutError("Timeout waiting for runs to complete.")
        time.sleep(poll_interval)
    return run_statuses
