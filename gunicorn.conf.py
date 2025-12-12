import multiprocessing
from dotenv import load_dotenv

load_dotenv()


# Server socket
bind = "127.0.0.1:5000"

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"

# Timeout for AI-powered features (grocery list, recipe generation)
timeout = 300  # 5 minutes to accommodate AI processing time

# Logging
accesslog = "-"
errorlog = "-"

# Process naming
proc_name = "recipez"
