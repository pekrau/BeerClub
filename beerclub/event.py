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
                event['account'] == self.current_user['email']):
            self.set_error_flash('You may not view the event data.')
            self.see_other('home')
            return
        self.render('event.html', event=event)


class Purchase(RequestHandler):
    "Buying one beverage. Always by the currently logged in account."

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
            saver['account'] = self.current_user['email']
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
    "Repayment to increase the credit of an account."

    @tornado.web.authenticated
    def get(self, email):
        self.check_admin()
        try:
            account = self.get_account(email, check=True)
        except KeyError:
            self.see_other('home')
        else:
            self.render('repayment.html', account=account)

    @tornado.web.authenticated
    def post(self, email):
        self.check_admin()
        try:
            account = self.get_account(email, check=True)
        except KeyError:
            self.see_other('home')
            return
        pid =self.get_argument('payment')
        for payment in settings['REPAYMENT']:
            if pid == payment['identifier']: break
        else:
            raise KeyError("no such repayment %s" % pid)
        with EventSaver(rqh=self) as saver:
            saver['account'] = account['email']
            saver['action']  = constants.REPAYMENT
            saver['payment'] = payment['identifier']
            saver['credit']  = int(self.get_argument('amount'))
            saver['date']    = self.get_argument('date', utils.today())
        self.see_other('accounts')
