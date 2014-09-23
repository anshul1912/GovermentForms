#!/usr/bin/env python
# coding: utf-8

import tornado.ioloop
import tornado.web

import psycopg2
import momoko
import redis

from settings import SETTINGS
from urls import ROUTES

application = tornado.web.Application(ROUTES, **SETTINGS)
application.db = momoko.Pool(dsn="dbname=%s user=%s password=%s host=%s port=%s" %
    (SETTINGS.get('db_name'), SETTINGS.get('db_user'), SETTINGS.get('db_pass'),
        SETTINGS.get('db_host'), SETTINGS.get('db_port')
    ))

application.mc = redis.StrictRedis(
        host=SETTINGS.get('redis_host', 'localhost'),
        port=SETTINGS.get('redis_port', 6379),
        db=0,
        password=SETTINGS.get('redis_pass', None)
    )

if __name__ == '__main__':
    application.listen(5000)
    tornado.ioloop.IOLoop.instance().start()
