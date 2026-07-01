"""
Gunicorn production configuration for CTF Arena v2.
Usage: gunicorn -c deployment/gunicorn.conf.py "app:create_app('production')"
"""
import multiprocessing
import os

# Server socket
bind = os.environ.get("GUNICORN_BIND", "127.0.0.1:8000")
backlog = 2048

# Workers
workers = int(os.environ.get("GUNICORN_WORKERS", multiprocessing.cpu_count() * 2 + 1))
worker_class = os.environ.get("GUNICORN_WORKER_CLASS", "sync")
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
timeout = int(os.environ.get("GUNICORN_TIMEOUT", 30))
keepalive = 2
graceful_timeout = 30

# Logging
accesslog = os.environ.get("GUNICORN_ACCESS_LOG", "-")
errorlog = os.environ.get("GUNICORN_ERROR_LOG", "-")
loglevel = os.environ.get("GUNICORN_LOG_LEVEL", "info")
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name = "ctf-arena"

# Server mechanics
daemon = False
pidfile = os.environ.get("GUNICORN_PID_FILE", "/tmp/ctf-arena.pid")
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL (optional - usually handled by Nginx)
# keyfile = "/path/to/key.pem"
# certfile = "/path/to/cert.pem"

def on_starting(server):
    server.log.info("CTF Arena is starting...")

def worker_exit(server, worker):
    server.log.info(f"Worker {worker.pid} exited.")
