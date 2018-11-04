"Home page, and misc others."

import tornado.web

from beerclub import constants
from beerclub import settings
from beerclub import utils
from beerclub.requesthandler import RequestHandler


class Home(RequestHandler):
    "Home page; login or payment and member info."

    def get(self):
        if self.current_user:
            self.current_user['balance'] = self.get_balance(self.current_user)
            self.current_user['count'] = self.get_count(self.current_user)
            self.render('home_member.html')
        else:
            self.render('home_login.html')


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
