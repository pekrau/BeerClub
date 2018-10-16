#!/usr/bin/python2
"A web application to keep track of the beer tabs for registered users."

import logging
import os

import tornado.web
import tornado.ioloop

from beerclub import utils
from beerclub import settings
from beerclub import uimodules

from beerclub.requesthandler import RequestHandler
from beerclub.account import (Account,
                              AccountEdit,
                              Accounts,
                              Login,
                              Logout,
                              Reset,
                              Password,
                              Register,
                              Enable,
                              Disable)
from beerclub.event import (Event,
                            Purchase)


class Home(RequestHandler):
    "Home page; login or payment and account info."

    def get(self):
        if self.current_user:
            self.render('home_account.html',
                        beverages_count=self.get_beverages_count(),
                        home_active=True)
        else:
            self.render('home_login.html', home_active=False)


def main():
    url = tornado.web.url
    handlers = [url(r'/', Home, name='home'),
                url(r'/purchase', Purchase, name='purchase'),
                url(r'/event/([0-9a-f]{32})', Event, name='event'),
                url(r'/account/([^/]+)', Account, name='account'),
                url(r'/account/([^/]+)/edit', AccountEdit, name='account_edit'),
                url(r'/account/([^/]+)/enable', Enable, name='enable'),
                url(r'/account/([^/]+)/disable', Disable, name='disable'),
                url(r'/accounts', Accounts, name='accounts'),
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
        ui_modules=uimodules,
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
    
