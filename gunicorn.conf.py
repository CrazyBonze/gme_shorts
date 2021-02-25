import multiprocessing

print("Starting application")


bind = "0.0.0.0:5000"
name = 'hello'
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = 'gevent'
accesslog = 'log'
loglevel = 'info'
