"User interface modules."

import locale
import logging

import tornado.web

from . import constants
from . import settings
from . import utils


class Money(tornado.web.UIModule):
    "HTML for a money value."

    def render(self, money, currency=True, padding=6):
        value = locale.currency(money, symbol=currency, grouping=True)
        padding = '&nbsp;' * max(0, padding - len(str(int(money))))
        value = padding + value
        if money >= 0:
            return '<span class="text-monospace">%s</span>' % value
        else:
            return '<strong class="text-monospace text-danger">%s</strong>' % value

class Status(tornado.web.UIModule):
    "HTML for account status."

    def render(self, account):
        if account['status'] == constants.DISABLED:
            return '<strong class="text-danger">disabled</strong>'
        elif account['status'] == constants.PENDING:
            return '<strong class="text-warning">pending</strong>'
        else: 
            return account['status']

class Role(tornado.web.UIModule):
    "HTML for account role."

    def render(self, account):
        if account['role'] == constants.ADMIN:
            return '<strong class="text-danger">admin</strong>'
        else: 
            return account['role']

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

class Step(tornado.web.UIModule):
    "Step to next item in list and output whenever there is a new value."

    def render(self, value, items, store):
        if value == store.get('value'):
            pos = store.get('pos')
            if pos is None:
                pos = 0
        else:
            pos = store.get('pos')
            if pos is None:
                pos = 0
            else:
                pos += 1
                if pos >= len(items):
                    pos = 0
        store['pos'] = pos
        store['value'] = value
        return items[pos]

class Date(tornado.web.UIModule):
    "Output the date; today if no value given."

    def render(self, date=None):
        if date is None:
            return utils.today()
        else:
            return date
