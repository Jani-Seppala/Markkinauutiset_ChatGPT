from openai import OpenAI
import tiktoken
import datetime
import pytz
from app import mongo

client = OpenAI()

# encoding = tiktoken.get_encoding("cl100k_base")
encoding = tiktoken.encoding_for_model('gpt-3.5-turbo')

# Connect to the MongoDB database
news_collection = mongo.db.news
analysis_collection = mongo.db.analysis

prompt = """You are expert in financial analysis. Your job is to analyse company news articles in. They contains information ranging from financial results, management stock transactions, to general company updates. Identify the main event(s) described in the news, including any significant numbers and business jargon. Provide a summary that clarifies:

- The type of the news (financial results, stock transaction, general update, etc.)
- A breakdown and simple explanation of any complex financial data or business terms mentioned
- An evaluation of how this news could impact the company's future, categorizing the impact as positive, negative, or neutral.

Ensure the analysis is presented in simple terms so that someone without a background in business or finance can easily understand it. Highlight any important context or implications that might not be immediately obvious to a layperson. The news articles can be in english or finnish language but I want that you answer in finnish only."""

# Fetch news items from MongoDB
news_items = news_collection.find({})


def num_tokens_from_string(string: str, encoding_name: str) -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens

for news_item in news_items:
    # Check if analysis already exists for this news item
    existing_analysis = analysis_collection.find_one({"news_id": news_item["_id"]})
    
    if existing_analysis is not None:
        print(f"Analysis for news item {news_item['_id']} already exists. Skipping.")
        continue
      
    # Construct the prompt with the actual news content
    actual_prompt = prompt + "\n\n" + news_item["messageUrlContent"]
    
    # total prompt tokens if needed later
    actual_prompt_tokens = num_tokens_from_string(actual_prompt, "cl100k_base")

    print(actual_prompt)
    print(f'--------------------------------------{actual_prompt_tokens}--------------------------------------')
    
    completion = client.chat.completions.create(
      model="gpt-3.5-turbo",
      messages=[
        {"role": "system", "content": f"{prompt}"},
        {"role": "user", "content": f"{news_item["messageUrlContent"]}"},
      ],
      temperature=0.5,
    )

    # print(completion.choices[0].message)
    
    # Extract the generated analysis
    
    
    # analysis_content = completion.choices[0].message
    analysis_content = completion.choices[0].message.content
    cet_timezone = pytz.timezone('CET')
    now_cet = datetime.datetime.now(cet_timezone)

    # Format the timestamp as a string to match the "releaseTime" format in the news collection
    created_at_formatted = now_cet.strftime('%Y-%m-%d %H:%M:%S')

    # Save the analysis with the formatted timestamp
    analysis_collection.insert_one({
        "news_id": news_item["_id"],
        "analysis_content": analysis_content,
        "created_at": created_at_formatted
    })

    
    print(analysis_content)
    print('----------------------------------------------------------------------------')
    print(f"Analysis for news item {news_item['_id']} saved.")
    
  