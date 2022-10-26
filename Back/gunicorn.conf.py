import os
bind = "127.0.0.1:8001"
workers = 3

if os.getenv("DJANGO_ENV") == "live":
    certfile = '/etc/letsencrypt/live/hobbyshare.app/fullchain.pem'
    keyfile = '/etc/letsencrypt/live/hobbyshare.app/privkey.pem'

log_file = '-'