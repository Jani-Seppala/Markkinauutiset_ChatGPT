from openai import OpenAI
import tiktoken
import os
import logging
import time

client = OpenAI()


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


def analyze_news(news_item, stock_info):
    """Generates an analysis for a given news item and associated stock price data."""
    
    start_time = time.time()
    # prompt = ""
    try:
        PROMPT = load_prompt()
        if not PROMPT:
            logging.warning("Failed to load prompt. Skipping news item analysis.")
            return "Failed to load prompt.", None
        if 'messageUrlContent' not in news_item:
            return ("Error: 'messageUrlContent' not found in news_item", PROMPT)
        
        prompt = PROMPT.format(stock_data=stock_info, news_item=news_item['messageUrlContent'])

        # print(prompt)

        max_tokens = 100000
        number_of_tokens = num_tokens_from_string(prompt, "cl100k_base")
        
        if number_of_tokens > max_tokens:
            return (f"Error: The prompt is too long ({number_of_tokens} tokens, exceeds {max_tokens} tokens).", prompt)
            
        
        logging.info(f"Prompt contains {number_of_tokens} tokens in openAiApiCall.py")
    
        model_used = "gpt-4o"
        logging.info("Sending request to OpenAI...")
        completion = client.chat.completions.create(
            # model="gpt-3.5-turbo",
            # model="gpt-4-turbo",
            model=model_used,
            messages=[
                {"role": "system", "content": prompt}
            ],
            temperature=0.5,
            # temperature=1,
        )

        # Extract the generated analysis
        analysis_content = completion.choices[0].message.content
        elapsed_time = time.time() - start_time
        logging.info(f"Received response from OpenAI in {elapsed_time:.2f} seconds.")
        return analysis_content, prompt, model_used

    except Exception as e:
        elapsed_time = time.time() - start_time
        logging.error(f"An error occurred in analyze_news after {elapsed_time:.2f} seconds: {e}")
        return (f"An error occurred in analyze_news: {str(e)}", prompt, None)


def num_tokens_from_string(string: str, encoding_name: str) -> int:
    """Returns the number of tokens in a text string."""
    try:
        encoding = tiktoken.get_encoding(encoding_name)
        num_tokens = len(encoding.encode(string))
        return num_tokens
    except Exception as e:
        logging.warning(f"Error calculating tokens: {str(e)}")
        return -1  # Return -1 or another indicator for error in token calculation