"Home page, and misc others."

import csv
from cStringIO import StringIO

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
    "Display snapshots table."

    @tornado.web.authenticated
    def get(self):
        self.check_admin()
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


class SnapshotsCsv(Snapshots):
    "Output CSV for snapshots data."

    def render(self, template, snapshots, from_, to):
        csvbuffer = StringIO()
        writer = csv.writer(csvbuffer)
        row = ['Date',
               'BeerClub',
               'members',
               'surplus']
        row.extend(constants.STATUSES)
        writer.writerow(row)
        for snapshot in snapshots:
            row = [snapshot['date'],
                   snapshot['beerclub_balance'],
                   snapshot['members_balance'],
                   snapshot['beerclub_balance'] - snapshot['members_balance']]
            for status in constants.STATUSES:
                row.append(snapshot['member_counts'][status])
            writer.writerow(row)
        self.write(csvbuffer.getvalue())
        self.set_header('Content-Type', constants.CSV_MIME)
        filename = "snapshots_%s_%s.csv" % (from_, to)
        self.set_header('Content-Disposition', 
                        'attachment; filename="%s"' % filename)


class Dashboard(RequestHandler):
    "Dashboard display of various interesting data."

    @tornado.web.authenticated
    def get(self):
        self.check_admin()
        self.render('dashboard.html')


class BalanceCsv(Snapshots):
    "Output CSV for snapshots balance data."

    def render(self, template, snapshots, from_, to):
        csvbuffer = StringIO()
        writer = csv.writer(csvbuffer)
        row = ['date',
               'amount',
               'type']
        row.extend(constants.STATUSES)
        writer.writerow(row)
        for snapshot in snapshots:
            row = [snapshot['date'], snapshot['beerclub_balance'], 'beerclub']
            writer.writerow(row)
            row[1] = snapshot['members_balance']
            row[2] = 'members'
            writer.writerow(row)
            row[1] = snapshot['beerclub_balance'] - snapshot['members_balance']
            row[2] = 'surplus'
            writer.writerow(row)
        self.write(csvbuffer.getvalue())
        self.set_header('Content-Type', constants.CSV_MIME)

