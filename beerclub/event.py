"Event: payment, etc."

import logging

import tornado.web

from . import constants
from . import settings
from . import utils
from .requesthandler import RequestHandler
from .saver import Saver


class EventSaver(Saver):
    doctype = constants.EVENT


class Event(RequestHandler):
    "View an event; payment or other."

    @tornado.web.authenticated
    def get(self, iuid):
        event = self.get_doc(iuid)
        # View access privilege
        if not (self.is_admin() or
                event['member'] == self.current_user['email']):
            self.set_error_flash('You may not view the event data.')
            self.see_other('home')
            return
        self.render('event.html', event=event)


class Purchase(RequestHandler):
    "Buying one beverage. Always by the currently logged in member."

    @tornado.web.authenticated
    def post(self):
        bid =self.get_argument('beverage')
        for beverage in settings['BEVERAGE']:
            if bid == beverage['identifier']: break
        else:
            raise KeyError("no such beverage %s" % bid)
        pid =self.get_argument('payment')
        for payment in settings['PAYMENT']:
            if pid == payment['identifier']: break
        else:
            raise KeyError("no such payment %s" % pid)
        with EventSaver(rqh=self) as saver:
            saver['member']   = self.current_user['email']
            saver['action']   = constants.PURCHASE
            saver['beverage'] = beverage['identifier']
            saver['price']    = beverage['price']
            saver['payment']  = payment['identifier']
            if payment['change']:
                saver['credit'] = - beverage['price']
            else:
                saver['credit'] = 0
        self.set_message_flash("Your purchased one %s." % beverage['label'])
        self.see_other('home')


class Repayment(RequestHandler):
    "Repayment to increase the credit of a member."

    @tornado.web.authenticated
    def get(self, email):
        self.check_admin()
        try:
            member = self.get_member(email, check=True)
        except KeyError:
            self.see_other('home')
        else:
            self.render('repayment.html', member=member)

    @tornado.web.authenticated
    def post(self, email):
        self.check_admin()
        try:
            member = self.get_member(email, check=True)
        except KeyError:
            self.see_other('home')
            return
        pid =self.get_argument('payment')
        for payment in settings['REPAYMENT']:
            if pid == payment['identifier']: break
        else:
            raise KeyError("no such repayment %s" % pid)
        with EventSaver(rqh=self) as saver:
            saver['member']  = member['email']
            saver['action']  = constants.REPAYMENT
            saver['payment'] = payment['identifier']
            saver['credit']  = float(self.get_argument('amount'))
            saver['date']    = self.get_argument('date', utils.today())
        self.see_other('members')

        
class Expenditure(RequestHandler):
    "Expenditure that reduces the BeerClub master member."

    @tornado.web.authenticated
    def get(self):
        self.check_admin()
        self.render('expenditure.html')

    @tornado.web.authenticated
    def post(self):
        self.check_admin()
        with EventSaver(rqh=self) as saver:
            saver['member'] = constants.BEERCLUB
            saver['action'] = constants.EXPENDITURE
            saver['credit'] = - float(self.get_argument('amount'))
            saver['date']   = self.get_argument('date', utils.today())
            saver['description'] = self.get_argument('description', None)
        self.see_other('ledger')


class Accounts(RequestHandler):
    "View event accounts for a member."

    def initialize(self, all):
        self.all = all

    @tornado.web.authenticated
    def get(self, email):
        try:
            member = self.get_member(email, check=True)
        except KeyError:
            self.see_other('home')
            return 
        if self.all:
            kwargs = dict()
        else:
            kwargs = dict(limit=settings['DISPLAY_ACCOUNTS_EVENTS'])
        events = self.get_docs('event/member',
                               key=[member['email'], constants.CEILING],
                               last=[member['email'], ''],
                               descending=True,
                               **kwargs)
        self.render('accounts.html',
                    member=member,
                    events=events, 
                    all=self.all,
                    show_event_links=True,
                    show_member_col=False)


class Activity(RequestHandler):
    "Members having made credit-affecting purchases recently."

    @tornado.web.authenticated
    def get(self):
        self.check_admin()
        activity = dict()
        first = utils.today(-settings['DISPLAY_ACTIVITY_DAYS'])
        last = utils.today()
        view = self.db.view('event/activity')
        for row in view[first : last+constants.CEILING]:
            try:
                activity[row.value] = max(activity[row.value], row.key)
            except KeyError:
                activity[row.value] = row.key
        activity.pop(constants.BEERCLUB, None)
        activity = activity.items()
        activity.sort(key=lambda i: i[1])
        members = []
        for email, timestamp in activity:
            member = self.get_member(email)
            member['activity'] = timestamp
            members.append(member)
        self.render('activity.html', members=members)


class Ledger(RequestHandler):
    "Ledger page for listing recent events."

    @tornado.web.authenticated
    def get(self):
        "Display recent events."
        result = list(self.db.view('event/ledger', group=False))
        if result:
            balance = result[0].value
        else:
            balance = 0
        try:
            from_ = self.get_argument('from')
        except tornado.web.MissingArgumentError:
            from_ = utils.today(-settings['DISPLAY_LEDGER_DAYS'])
        try:
            to = self.get_argument('to')
        except tornado.web.MissingArgumentError:
            to = utils.today()
        events = self.get_docs('event/ledger',
                               key=from_,
                               last=to+constants.CEILING)
        self.render('ledger.html',
                    balance=balance,
                    events=events,
                    from_=from_,
                    to=to,
                    show_event_links=self.is_admin(),
                    show_member_col=self.is_admin())
