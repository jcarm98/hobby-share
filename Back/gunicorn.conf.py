import os
bind = "127.0.0.1:8001"
workers = 3

if os.getenv("DJANGO_ENV") == "live":
    certfile = f'/etc/letsencrypt/live/{os.getenv("DJANGO_HOST")}/fullchain.pem'
    keyfile = f'/etc/letsencrypt/live/{os.getenv("DJANGO_HOST")}/privkey.pem'

log_file = '-'
