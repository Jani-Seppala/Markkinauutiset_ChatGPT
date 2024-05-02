from openai import OpenAI
import tiktoken
import os

client = OpenAI()


def load_prompt():
    # Try to get the prompt from an environment variable
    prompt = os.getenv('PROMPT_TEMPLATE')
    
    # If the environment variable is not set, read from a local file
    if prompt is None:
        try:
            with open('prompt.txt', 'r') as file:
                prompt = file.read()
        except FileNotFoundError:
            print("Prompt file not found and no environment variable set. Using default prompt.")
            prompt = f"An error occurred: {str(FileNotFoundError)}"
    
    return prompt


def analyze_news(news_item, stock_info):
    """Generates an analysis for a given news item and associated stock price data."""
    
    try:
        
        PROMPT = load_prompt()
        if not PROMPT:
            print("Failed to load prompt. Skipping news item analysis.")
            return "Failed to load prompt.", None
        if 'messageUrlContent' not in news_item:
            return ("Error: 'messageUrlContent' not found in news_item", PROMPT)
        
        prompt = PROMPT.format(stock_info=stock_info, news_item=news_item['messageUrlContent'])

        # print(prompt)

        max_tokens = 100000
        number_of_tokens = num_tokens_from_string(prompt, "cl100k_base")
        
        if number_of_tokens > max_tokens:
            return (f"Error: The prompt is too long ({number_of_tokens} tokens, exceeds {max_tokens} tokens).", prompt)
            
        
        print(f"Prompt contains {number_of_tokens} tokens in openAiApiCall.py")
    
        completion = client.chat.completions.create(
            # model="gpt-3.5-turbo",
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": prompt}
            ],
            temperature=0.5,
        )

        # Extract the generated analysis
        analysis_content = completion.choices[0].message.content
        return analysis_content, prompt

    except Exception as e:
        return (f"An error occurred in analyze_news: {str(e)}", prompt)


def num_tokens_from_string(string: str, encoding_name: str) -> int:
    """Returns the number of tokens in a text string."""
    try:
        encoding = tiktoken.get_encoding(encoding_name)
        num_tokens = len(encoding.encode(string))
        return num_tokens
    except Exception as e:
        print(f"Error calculating tokens: {str(e)}")
        return -1  # Return -1 or another indicator for error in token calculation