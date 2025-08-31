# Gunicorn configuration file
import multiprocessing

# Server socket
bind = "0.0.0.0:8000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
timeout = 30
keepalive = 2

# Restart workers after this many requests, to help prevent memory leaks
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Process naming
proc_name = "badminton-rating"

# Server mechanics
daemon = False
pidfile = "/tmp/badminton-rating.pid"
user = None
group = None
tmp_upload_dir = None

# SSL (if needed)
# keyfile = "path/to/keyfile"
# certfile = "path/to/certfile"

