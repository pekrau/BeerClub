"User interface modules."

import logging

import tornado.web

from . import constants
from . import settings
from . import utils


class Money(tornado.web.UIModule):
    "HTML for a money value."

    FORMAT = '<span class="text-monospace text-nowrap %s" style="margin-left: %sch;">%s</span>'

    def render(self, money, currency=True, padding=5):
        if money is None: money = 0
        fmt = "{:.%if}" % settings['MONEY_DECIMAL_PLACES']
        value = fmt.format(money)
        minus = value[:1] == '-'
        if minus:
            value = value[1:]
        iv, dv = value.split('.')
        if settings['MONEY_THOUSAND_DELIMITER']:
            ivl = []
            while len(iv):
                ivl.append(iv[-3:])
                iv = iv[:-3]
            iv = settings['MONEY_THOUSAND_DELIMITER'].join(reversed(ivl))
        value = iv + settings['MONEY_DECIMAL_POINT'] + dv
        if minus:
            value = '-' + value
        if currency:
            value += ' ' + settings['CURRENCY']
        padding = max(0, padding - len(str(int(money)))) + 0.2
        for cutoff, klass in settings['CREDIT_CLASSES']:
            if money <= cutoff: break
        else:
            klass = ''
        return self.FORMAT % (klass, padding, value)

class Status(tornado.web.UIModule):
    "HTML for member status."

    def render(self, member):
        if member['status'] == constants.ENABLED:
            return '<strong class="text-success">%s</strong>' % member['status']
        elif member['status'] == constants.DISABLED:
            return '<strong class="text-danger">disabled</strong>'
        elif member['status'] == constants.PENDING:
            return '<strong class="text-warning">pending</strong>'
        else: 
            return member['status']

class Role(tornado.web.UIModule):
    "HTML for member role."

    def render(self, member):
        if member['role'] == constants.ADMIN:
            return '<strong class="text-danger">admin</strong>'
        else: 
            return member['role']

class LastLogin(tornado.web.UIModule):
    "HTML for member last login."

    def render(self, member):
        if member.get('last_login'):
            return '<span class="localtime small">%s</span>' % member['last_login']
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
