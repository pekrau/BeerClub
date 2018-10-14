"Event: payment, etc."

import logging

import tornado.web

from . import constants
from . import utils
from .requesthandler import RequestHandler
from .saver import Saver


class EventSaver(Saver):
    doctype = constants.EVENT

    def finalize(self):
        "Set the log fields for the event."
        self['timestamp'] = utils.timestamp()
        self['date'] = utils.today()
        if self.rqh:
            # xheaders argument to HTTPServer takes care of X-Real-Ip
            # and X-Forwarded-For
            self['remote_ip'] = self.rqh.request.remote_ip
            try:
                self['user_agent'] = self.rqh.request.headers['User-Agent']
            except KeyError:
                pass
        if self.account:
            try:
                self['account'] = self.account['email']
            except (TypeError, AttributeError, KeyError):
                pass


class Event(RequestHandler):

    @tornado.web.authenticated
    def get(self, iuid):
        # XXX
        pass
