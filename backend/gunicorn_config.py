import logging
import subprocess
import sys
# from config2 import SocketIO

bind = "0.0.0.0:8080"
workers = 1
worker_class = 'eventlet'  # Use eventlet worker for WebSocket support
    
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