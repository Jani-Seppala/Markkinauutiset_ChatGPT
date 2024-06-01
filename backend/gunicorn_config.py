# bind = "0.0.0.0:8080"
# workers = 1


import logging
import subprocess
import sys

bind = "0.0.0.0:8080"
workers = 1

def start_nasdaq_api_call():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s:%(levelname)s:%(message)s')
    logging.info("Starting nasdaqApiCall as a background process")
    logging.info(f"Python executable: {sys.executable}")
    subprocess.Popen([sys.executable, '-m', 'apicalls.nasdaqApiCall'])

def on_starting(server):
    start_nasdaq_api_call()