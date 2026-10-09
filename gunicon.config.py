import multiprocessing, os
bind = f"0.0.0.0:{os.getenv('PORT', '8000')}"
workers = int(os.getenv("WEB_CONCURRENCY", multiprocessing.cpu_count() * 2 + 1))
worker_class = "uvicorn.workers.UvicornWorker"
timeout = 60
keepalive = 5
accesslog = "-"
errorlog = "-"
loglevel = "info"