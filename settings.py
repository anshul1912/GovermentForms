# coding: utf-8
import os

DEBUG = True
DOMAIN = "cp.knowledgeashram.com"

DB_NAME = 'mydb'
DB_HOST = 'localhost'
DB_PORT = '5432'
DB_USER = 'a141982112'
DB_PASS = ''

REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_PASS = None

PASSWORD_SALT = '4c9194df-82b6-4cc3-9f7b-a8b8d626b858'
COOKIE_SALT = '3e26af25-375e-4dfc-841e-80892349f509'

STATIC_ROOT = os.path.join(os.path.dirname(__file__), "presentation", "static")
UPLOAD_ROOT = os.path.join(os.path.dirname(__file__), "uploads")
TEMPLATES = os.path.join("presentation", "templates")

FACEBOOK_API_KEY = ''
FACEBOOK_SECRET = ''

TWITTER_CONSUMER_KEY = ''
TWITTER_CONSUMER_SECRET = ''

try:
    from local_settings import *
except:
    pass

SETTINGS = dict(
    gzip=True,
    debug=DEBUG,
    auto_reload=DEBUG,
    login_url='/auth/login',
    post_login_redirect_url='/',
    static_path=STATIC_ROOT,
    template_path=TEMPLATES,
    upload_path=UPLOAD_ROOT,
    autoescape=None,
    xsrf_cookies=False,
    password_salt=os.environ.get('BSALT', PASSWORD_SALT),
    cookie_secret=os.environ.get('BSALT', COOKIE_SALT),

    # google_consumer_key=os.environ.get('GOOGLE_CONSUMER_KEY', ''),
    # google_consumer_secret=os.environ.get('GOOGLE_CONSUMER_SECRET', ''),

    facebook_redirect_uri='http://%s/auth/facebook' % DOMAIN,
    facebook_api_key=os.environ.get('FACEBOOK_API_KEY', FACEBOOK_API_KEY),
    facebook_secret=os.environ.get('FACEBOOK_SECRET', FACEBOOK_SECRET),

    twitter_consumer_key=os.environ.get('TWITTER_CONSUMER_KEY', TWITTER_CONSUMER_KEY),
    twitter_consumer_secret=os.environ.get('TWITTER_CONSUMER_SECRET', TWITTER_CONSUMER_SECRET),

    db_name=DB_NAME,
    db_host=DB_HOST,
    db_port=DB_PORT,
    db_user=DB_USER,
    db_pass=DB_PASS,

    redis_host=REDIS_HOST,
    redis_port=REDIS_PORT,
    redis_pass=REDIS_PASS,

    session_timeout=3600, # one hour in seconds
    PACKAGE = {
        '0' : 'Demo',
        '1' : '6000.00',
        '2' : '5400.00',
        '3' : '4800.00',
        '4' : '4200.00',
    },

    merchant = {
        'key' : 'C0Dr8m', # C0Dr8m for test key
        'salt' : '3sf0jURk', # 3sf0jURk for test salt
    },
)
