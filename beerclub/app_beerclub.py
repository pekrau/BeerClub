#!/usr/bin/python2
"A web application to keep track of the beer tabs for registered users."

from __future__ import print_function

import logging
import os
import urlparse

import tornado.web
import tornado.ioloop

import beerclub
from beerclub import settings

from beerclub.home import Home

def setup():
    parts = urlparse.urlparse(settings['BASE_URL'])
    settings['PORT'] = parts.port or 80
    if settings.get('LOGGING_DEBUG'):
        kwargs = dict(level=logging.DEBUG)
    else:
        kwargs = dict(level=logging.INFO)
    try:
        kwargs['format'] = settings['LOGGING_FORMAT']
    except KeyError:
        pass
    logging.basicConfig(**kwargs)
    logging.info("BeerClub version %s", beerclub.__version__)
    logging.info("ROOT_DIR: %s", settings['ROOT_DIR'])
    logging.info("logging debug: %s", settings['LOGGING_DEBUG'])
    logging.info("tornado debug: %s", settings['TORNADO_DEBUG'])


def main():
    url = tornado.web.url
    handlers = [url(r'/', Home, name='home')]

    application = tornado.web.Application(
        handlers=handlers,
        debug=settings.get('TORNADO_DEBUG', False),
        cookie_secret=settings['COOKIE_SECRET'],
        xsrf_cookies=True,
        # ui_modules=uimodules,
        template_path=os.path.join(settings['ROOT_DIR'], 'html'),
        static_path=os.path.join(settings['ROOT_DIR'], 'static'),
        # login_url=r'/login',
    )
    application.listen(settings['PORT'], xheaders=True)
    logging.info("web server %s", settings['BASE_URL'])
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    setup()
    main()
    
