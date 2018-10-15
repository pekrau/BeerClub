#!/usr/bin/python2
"A web application to keep track of the beer tabs for registered users."

import logging
import os

import tornado.web
import tornado.ioloop

from beerclub import utils
from beerclub import settings

from beerclub.requesthandler import RequestHandler
from beerclub.account import (Account,
                              AccountEdit,
                              Login,
                              Logout,
                              Reset,
                              Password,
                              Register)
from beerclub.event import (Event,
                            Purchase)


class Home(RequestHandler):
    "Home page; login or payment and account info."

    def get(self):
        if self.current_user:
            self.render('home_account.html')
        else:
            self.render('home_anon.html')


def main():
    url = tornado.web.url
    handlers = [url(r'/', Home, name='home'),
                url(r'/purchase', Purchase, name='purchase'),
                url(r'/event/([0-9a-f]{32})', Event, name='event'),
                url(r'/account/([^/]+)', Account, name='account'),
                url(r'/account/([^/]+)/edit', AccountEdit, name='account_edit'),
                url(r'/login', Login, name='login'),
                url(r'/logout', Logout, name='logout'),
                url(r'/reset', Reset, name='reset'),
                url(r'/password', Password, name='password'),
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
    
