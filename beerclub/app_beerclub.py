"A web application to keep track of the beer tabs for registered users."

import logging
import os

import tornado.web
import tornado.ioloop

from beerclub import settings
from beerclub import uimodules
from beerclub import utils
from beerclub.home import (Home,
                           Snapshots,
                           SnapshotsCsv,
                           Dashboard,
                           BalanceCsv)
from beerclub.member import (Member,
                             Settings,
                             Members,
                             MembersCsv,
                             Pending,
                             Login,
                             Logout,
                             Reset,
                             Password,
                             Register,
                             Enable,
                             Disable,
                             MemberApiV1)
from beerclub.event import (Event,
                            Purchase,
                            Payment,
                            Load,
                            Expenditure,
                            Cash,
                            Account,
                            Activity,
                            Ledger,
                            LedgerCsv,
                            Payments,
                            PaymentsCsv,
                            EventApiV1,
                            MemberEventApiV1)

def main():
    url = tornado.web.url
    handlers = [
        url(r'/', Home, name='home'),
        url(r'/purchase', Purchase, name='purchase'),
        url(r'/purchase/([^/]+)', Purchase, name='purchase_member'),
        url(r'/payment/([^/]+)', Payment, name='payment'),
        url(r'/load', Load, name='load'),
        url(r'/member/([^/]+)', Member, name='member'),
        url(r'/settings/([^/]+)', Settings, name='settings'),
        url(r'/enable/([^/]+)', Enable, name='enable'),
        url(r'/disable/([^/]+)', Disable, name='disable'),
        url(r'/activity', Activity, name='activity'),
        url(r'/pending', Pending, name='pending'),
        url(r'/members', Members, name='members'),
        url(r'/members.csv', MembersCsv, name='members_csv'),
        url(r'/account/([^/]+)', Account, name='account'),
        url(r'/expenditure', Expenditure, name='expenditure'),
        url(r'/cash', Cash, name='cash'),
        url(r'/ledger', Ledger, name='ledger'),
        url(r'/ledger.csv', LedgerCsv, name='ledger_csv'),
        url(r'/payments', Payments, name='payments'),
        url(r'/payments.csv', PaymentsCsv, name='payments_csv'),
        url(r'/snapshots', Snapshots, name='snapshots'),
        url(r'/snapshots.csv', SnapshotsCsv, name='snapshots_csv'),
        url(r'/dashboard', Dashboard, name='dashboard'),
        url(r'/balance.csv', BalanceCsv, name='balance_csv'),
        url(r'/event/([0-9a-f]{32})', Event, name='event'),
        url(r'/login', Login, name='login'),
        url(r'/logout', Logout, name='logout'),
        url(r'/reset', Reset, name='reset'),
        url(r'/password', Password, name='password'),
        url(r'/register', Register, name='register'),
        url(r'/api/v1/event/([0-9a-f]{32})', EventApiV1, name='api_event'),
        url(r'/api/v1/member/([^/]+)', MemberApiV1, name='api_member'),
        url(r'/api/v1/event/member/([^/]+)',
            MemberEventApiV1, name='api_member_event'),
        url(r'/([^/]+)', tornado.web.StaticFileHandler,
            {'path': os.path.join(settings['ROOT_DIR'], 'static')}),
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
