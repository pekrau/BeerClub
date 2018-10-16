"User interface modules."

import logging

import tornado.web

from . import constants
from . import settings
from . import utils


class Status(tornado.web.UIModule):
    "HTML for account status."

    def render(self, account):
        if account['status'] == constants.DISABLED:
            return '<strong class="text-danger">disabled</strong>'
        elif account['status'] == constants.PENDING:
            return '<strong class="text-warning">pending</strong>'
        else: 
            return 'enabled'

class Credit(tornado.web.UIModule):
    "HTML for account credit."

    def render(self, account, currency=True):
        credit = self.handler.get_credit(account)
        if currency:
            value = "%s %s" % (credit, settings['CURRENCY'])
        else:
            value = str(credit)
        if credit >= 0:
            return value
        else:
            return '<strong class="text-danger">%s</strong>' % value

class LastLogin(tornado.web.UIModule):
    "HTML for account last login."

    def render(self, account):
        if account.get('last_login'):
            return '<span class="localtime">%s</span>' % account['last_login']
        else: 
            return '-'

class NavitemActive(tornado.web.UIModule):
    "Output active class depending on handler."

    def render(self, navbar):
        if self.handler.__class__.__name__.lower() == navbar:
            return 'active'
        else:
            return ''
