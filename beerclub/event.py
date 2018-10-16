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
        # XXX
        pass


class Purchase(RequestHandler):
    "Buying one beverage."

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
            raise KeyError("no such payment %s" % bid)
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
