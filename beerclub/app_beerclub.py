#!/usr/bin/python2
"A web application to keep track of the beer tabs for registered users."

import logging
import os

import tornado.web
import tornado.ioloop

from beerclub import utils
from beerclub import settings

from beerclub.home import Home
from beerclub.account import (Login,
                              Register)


def main():
    url = tornado.web.url
    handlers = [url(r'/', Home, name='home'),
                url(r'/login', Login, name='login'),
                url(r'/register', Register, name='register'),
    ]

    application = tornado.web.Application(
        handlers=handlers,
        debug=settings.get('TORNADO_DEBUG', False),
        cookie_secret=settings['COOKIE_SECRET'],
        xsrf_cookies=True,
        template_path=os.path.join(settings['ROOT_DIR'], 'html'),
        static_path=os.path.join(settings['ROOT_DIR'], 'static'),
        login_url=r'/',
    )
    application.listen(settings['PORT'], xheaders=True)
    logging.info("tornado debug: %s", settings['TORNADO_DEBUG'])
    logging.info("web server %s", settings['BASE_URL'])
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    utils.setup()
    utils.load_design_documents(utils.get_db())
    main()
    
