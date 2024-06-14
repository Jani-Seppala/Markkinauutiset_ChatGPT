import logging
import subprocess
import sys

bind = "0.0.0.0:8080"
workers = 2

# def start_nasdaq_api_call():
#     logging.basicConfig(level=logging.INFO, format='%(asctime)s:%(levelname)s:%(message)s')
#     logging.info("Starting nasdaqApiCall as a background process")
#     logging.info(f"Python executable: {sys.executable}")
#     subprocess.Popen([sys.executable, '-m', 'apicalls.nasdaqApiCall'])

# def on_starting(server):
#     start_nasdaq_api_call()
    
def post_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def pre_exec(server):
    server.log.info("Forked child, re-executing.")

def when_ready(server):
    server.log.info("Server is ready. Spawning workers")

def worker_int(worker):
    worker.log.info("worker received INT or QUIT signal")

def worker_abort(worker):
    worker.log.info("worker received SIGABRT signal")