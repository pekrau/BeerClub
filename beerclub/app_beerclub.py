#!/usr/bin/python2
"A web application to keep track of the beer tabs for registered users."

import logging
import os

import tornado.web
import tornado.ioloop

from beerclub import constants
from beerclub import settings
from beerclub import uimodules
from beerclub import utils

from beerclub.requesthandler import RequestHandler
from beerclub.member import (Member,
                             Settings,
                             Members,
                             Pending,
                             Login,
                             Logout,
                             Reset,
                             Password,
                             Register,
                             Enable,
                             Disable)
from beerclub.event import (Event,
                            Purchase,
                            Payment,
                            Expenditure,
                            Account,
                            Active,
                            Ledger,
                            MemberEventApiV1)


class Home(RequestHandler):
    "Home page; login or payment and member info."
    def get(self):
        if self.current_user:
            self.current_user['balance'] = self.get_balance(self.current_user)
            self.render('home_member.html',
                        beverages_count=self.get_beverages_count(self.current_user),
                        home_active=True)
        else:
            self.render('home_login.html', home_active=False)


class Snapshots(RequestHandler):
    "Display snapshots."
    def get(self):
        try:
            from_ = self.get_argument('from')
        except tornado.web.MissingArgumentError:
            from_ = utils.today(-settings['DISPLAY_SNAPSHOT_DAYS'])
        try:
            to = self.get_argument('to')
        except tornado.web.MissingArgumentError:
            to = utils.today()
        if from_ > to:
            snapshots = []
        else:
            snapshots = self.get_docs('snapshot/date',
                                      key=from_,
                                      last=to+constants.CEILING)
        self.render('snapshots.html',
                    snapshots=snapshots,
                    from_=from_,
                    to=to)


def main():
    url = tornado.web.url
    handlers = [
        url(r'/', Home, name='home'),
        url(r'/purchase', Purchase, name='purchase'),
        url(r'/payment/([^/]+)', Payment, name='payment'),
        url(r'/member/([^/]+)', Member, name='member'),
        url(r'/settings/([^/]+)', Settings, name='settings'),
        url(r'/enable/([^/]+)', Enable, name='enable'),
        url(r'/disable/([^/]+)', Disable, name='disable'),
        url(r'/active', Active, name='active'),
        url(r'/pending', Pending, name='pending'),
        url(r'/members', Members, name='members'),
        url(r'/account/([^/]+)', Account, name='account'),
        url(r'/expenditure', Expenditure, name='expenditure'),
        url(r'/ledger', Ledger, name='ledger'),
        url(r'/snapshots', Snapshots, name='snapshots'),
        url(r'/event/([0-9a-f]{32})', Event, name='event'),
        url(r'/login', Login, name='login'),
        url(r'/logout', Logout, name='logout'),
        url(r'/reset', Reset, name='reset'),
        url(r'/password', Password, name='password'),
        url(r'/register', Register, name='register'),
        url(r'/api/v1/event/([^/]+)', MemberEventApiV1, name='api_event'),
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
    utils.initialize()
    main()
