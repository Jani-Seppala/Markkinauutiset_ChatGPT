from openai import OpenAI
import tiktoken
import os
import logging
import time
import sys

client = OpenAI()

# assistant = client.beta.assistants.create(
#             name="Financial Analyst",
#             instructions="You are a financial analyst. Analyze stock market news and provide insights.",
#             model="gpt-4o-mini",  # Specify the appropriate model
#             )

def load_prompt():
        
    prompt = None
    
    # If the environment variable is not set, read from a local file
    if prompt is None:
        try:
            logging.info(f"Current working directory: {os.getcwd()}")
            # with open('prompt.txt', 'r') as file:
            with open('prompt.txt', 'r', encoding='utf-8') as file:
                prompt = file.read()
        except FileNotFoundError:
            logging.warning("Prompt file not found and no environment variable set. Using default prompt.")
            prompt = f"An error occurred: {str(FileNotFoundError)}"
    
    return prompt


def analyze_news(news_item, stock_info, thread_id=None):
    """Generates an analysis for a given news item and associated stock price data."""
    
    start_time = time.time()
    # prompt = ""
    try:
        # PROMPT = load_prompt()
        # if not PROMPT:
        #     logging.warning("Failed to load prompt. Skipping news item analysis.")
        #     return "Failed to load prompt.", None
        # if 'messageUrlContent' not in news_item:
        #     return ("Error: 'messageUrlContent' not found in news_item", PROMPT)
        
        # # prompt = PROMPT.format(stock_data=stock_info, news_item=news_item['messageUrlContent'])
        # prompt = PROMPT

        # # print(prompt)

        # max_tokens = 100000
        # number_of_tokens = num_tokens_from_string(prompt, "cl100k_base")
        
        # if number_of_tokens > max_tokens:
        #     return (f"Error: The prompt is too long ({number_of_tokens} tokens, exceeds {max_tokens} tokens).", prompt)
            
        
        # logging.info(f"Prompt contains {number_of_tokens} tokens in openAiApiCall.py")
    
        # if os.environ.get('FLASK_ENV') != 'production':
            # news_and_stock_data = f"Latest stock news: {news_item['messageUrlContent']}, Latest stock data: {stock_info}"
        news_and_stock_data = f"Latest stock news: {news_item}, Latest stock data: {stock_info}"
        # thread_id = news_item.get('thread_id', None)
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
            # assistant_id="asst_0DkQjeTlGeZ6CU5YQ8B2DDwa"
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
                    text_blocks = [block.text.value for block in latest_message.content if block.type == 'text']
                    analysis_content = " ".join(text_blocks)
                    logging.info(f"Analysis content: {analysis_content}, news_and_stock_data: {news_and_stock_data}, model: {model_used}, thread_id: {thread_id}")
                    return analysis_content, news_and_stock_data, model_used, thread_id
            return "No analysis content found.", None, None, thread_id
        else:
            return f"Run Status: {run.status}", None, None, thread_id
        
        # else:
            
        #     PROMPT = load_prompt()
        #     if not PROMPT:
        #         logging.warning("Failed to load prompt. Skipping news item analysis.")
        #         return "Failed to load prompt.", None
        #     if 'messageUrlContent' not in news_item:
        #         return ("Error: 'messageUrlContent' not found in news_item", PROMPT)
            
        #     # prompt = PROMPT.format(stock_data=stock_info, news_item=news_item['messageUrlContent'])
        #     prompt = PROMPT

        #     # print(prompt)

        #     max_tokens = 100000
        #     number_of_tokens = num_tokens_from_string(prompt, "cl100k_base")
            
        #     if number_of_tokens > max_tokens:
        #         return (f"Error: The prompt is too long ({number_of_tokens} tokens, exceeds {max_tokens} tokens).", prompt)
                
            
        #     logging.info(f"Prompt contains {number_of_tokens} tokens in openAiApiCall.py")
            
            
        #     model_used = "gpt-4o"
        #     logging.info("Sending request to OpenAI...")
        #     completion = client.chat.completions.create(
        #         model=model_used,
        #         messages=[
        #             {"role": "system", "content": prompt}
        #         ],
        #         temperature=0.5,
        #     )

        #     # Extract the generated analysis
        #     analysis_content = completion.choices[0].message.content
        #     elapsed_time = time.time() - start_time
        #     logging.info(f"Received response from OpenAI in {elapsed_time:.2f} seconds.")
        #     return analysis_content, prompt, model_used
            

    except Exception as e:
        elapsed_time = time.time() - start_time
        logging.error(f"An error occurred in analyze_news after {elapsed_time:.2f} seconds: {e}")
        # if os.environ.get('FLASK_ENV') != 'production':
        return (f"An error occurred in analyze_news: {str(e)}", news_and_stock_data, None, thread_id)
        # else:
        #     return (f"An error occurred in analyze_news: {str(e)}", news_and_stock_data, None, thread_id)


def num_tokens_from_string(string: str, encoding_name: str) -> int:
    """Returns the number of tokens in a text string."""
    try:
        encoding = tiktoken.get_encoding(encoding_name)
        num_tokens = len(encoding.encode(string))
        return num_tokens
    except Exception as e:
        logging.warning(f"Error calculating tokens: {str(e)}")
        return -1  # Return -1 or another indicator for error in token calculation