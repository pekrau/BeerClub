"Event: purchase, payment, etc."

import csv
import datetime
import logging
import tempfile
from io import StringIO

import openpyxl
import tornado.web

from . import constants
from . import settings
from . import utils
from .requesthandler import RequestHandler, ApiMixin
from .saver import Saver


class EventSaver(Saver):
    doctype = constants.EVENT

    def set(self, data):
        action = data.get('action')
        if action == constants.PURCHASE:
            self.set_purchase(**data)
        elif action == constants.PAYMENT:
            self.set_payment(**data)
        elif action == constants.TRANSFER:
            self.set_transfer(**data)
        else:
            raise ValueError('invalid action')

    def set_purchase(self, **kwargs):
        self['action'] = constants.PURCHASE
        pid = kwargs.get('purchase')
        for purchase in settings['PURCHASE']:
            if pid == purchase['identifier']: break
        else:
            raise ValueError("no such purchase %s" % pid)
        bid = kwargs.get('beverage')
        for beverage in settings['BEVERAGE']:
            if bid == beverage['identifier']: break
        else:
            beverage = None
        if beverage:
            self['beverage']    = beverage['identifier']
            self['description'] = purchase['identifier']
            if purchase['change']:
                self['credit'] = - beverage['price']
            else:
                self['credit'] = 0.0
            self.message = "You purchased one %s." % beverage['label']
        else:                   # Special case 'Swish lazy'
            self['beverage'] = 'unknown beverage'
            self['description'] = kwargs.get('description', '')
            if purchase['change'] and kwargs.get('amount'):
                self['credit'] = - kwargs.get('amount')
            else:
                self['credit'] = 0.0
            self.message = 'You purchased some beverage.'
        self['date'] = kwargs.get('date') or utils.today()

    def set_payment(self, **kwargs):
        self['action'] = constants.PAYMENT
        try:
            amount = float(kwargs['amount'])
        except (KeyError, ValueError, TypeError):
            raise ValueError('invalid amount')
        pid = kwargs.get('payment')
        if pid == constants.EXPENDITURE:
            self['description'] = "%s: %s" % (constants.EXPENDITURE,
                                              kwargs.get('description'))
            self['credit'] = - amount
        elif pid == constants.CASH:
            self['description'] = 'cash transfer'
            self['credit'] = amount
        else:
            for payment in settings['PAYMENT']:
                if pid == payment['identifier']: break
            else:
                raise ValueError("no such payment %s" % pid)
            self['description'] = payment['identifier']
            self['credit'] = amount
        self['date'] = kwargs.get('date') or utils.today()

    def set_transfer(self, **kwargs):
        self['action'] = constants.TRANSFER
        try:
            amount = float(kwargs['amount'])
        except (KeyError, ValueError, TypeError):
            raise ValueError('invalid amount')
        self['credit'] = amount
        self['description'] = kwargs.get('description')
        self['date'] = kwargs.get('date') or utils.today()


class Event(RequestHandler):
    "View an event; purchase, payment, etc. Admin may delete it."

    @tornado.web.authenticated
    def get(self, iuid):
        try:
            event = self.get_doc(iuid)
        except KeyError:
            self.set_error_flash('No such event.')
            self.see_other('account', self.current_user['email'])
        else:
            # Check view access privilege
            if self.is_admin() or event['member']==self.current_user['email']:
                self.render('event.html', event=event)
            else:
                self.set_error_flash('You may not view the event data.')
                self.see_other('home')

    @tornado.web.authenticated
    def post(self, iuid):
        "Delete the event."
        self.check_admin()
        event = self.get_doc(iuid)
        if self.get_argument('_http_method', None) == 'DELETE':
            self.db.delete(event)
        self.see_other('account', event['member'])


class Purchase(RequestHandler):
    "Buying one beverage."

    @tornado.web.authenticated
    def get(self, email=None):
        "This page for admin to record purchases on behalf of a member."
        self.check_admin()
        if email is None:
            member = self.current_user
        else:
            try:
                member = self.get_member(email, check=True)
            except KeyError as error:
                self.set_error_flash(str(error))
                self.see_other('home')
                return
        self.render('purchase.html', member=member)

    @tornado.web.authenticated
    def post(self, email=None):
        if email is None:
            member = self.current_user
        else:
            try:
                member = self.get_member(email, check=True)
            except KeyError as error:
                self.set_error_flash(str(error))
                self.see_other('home')
                return
        try:
            with EventSaver(rqh=self) as saver:
                saver['member'] = member['email']
                saver.set_purchase(purchase=self.get_argument('purchase',None),
                                   beverage=self.get_argument('beverage',None))
        except ValueError as error:
            self.set_error_flash(str(error))
        else:
            self.set_message_flash(saver.message)
        if email is None:
            self.see_other('home')
        else:
            self.see_other('account', member['email'])


class Payment(RequestHandler):
    "Payment to increase the credit of a member, or correction."

    @tornado.web.authenticated
    def get(self, email):
        self.check_admin()
        try:
            member = self.get_member(email, check=True)
        except KeyError as error:
            self.set_error_flash(str(error))
            self.see_other('home')
        else:
            member['balance'] = self.get_balance(member)
            self.render('payment.html', member=member)

    @tornado.web.authenticated
    def post(self, email):
        self.check_admin()
        try:
            member = self.get_member(email, check=True)
        except KeyError as error:
            self.set_error_flash(str(error))
            self.see_other('home')
            return
        try:
            try:
                amount = float(self.get_argument('amount', None))
            except (KeyError, ValueError, TypeError):
                amount = 0.0
            payment = self.get_argument('payment', None)
            if payment is None:
                raise ValueError('no payment type specified')
            if payment == constants.CORRECTION:
                with EventSaver(rqh=self) as saver:
                    saver['member'] = member['email']
                    saver.set_transfer(amount=amount,
                                       description='manual correction')
            else:
                with EventSaver(rqh=self) as saver:
                    saver['member'] = member['email']
                    saver.set_payment(payment=payment,
                                      amount=amount,
                                      date=self.get_argument('date', None))
                lazy = self.get_argument('swish_lazy', False)
                if lazy and lazy.lower() == 'true':
                    with EventSaver(rqh=self) as saver:
                        saver['action']      = constants.PURCHASE
                        saver['member']      = member['email']
                        saver['beverage']    = 'unknown beverage'
                        saver['description'] = 'Swish lazy'
                        saver['credit']      = - amount
        except ValueError as error:
            self.set_error_flash(str(error))
        self.see_other('account', member['email'])

        
class Load(RequestHandler):
    "Load payments data file, e.g. XLSX Swish records."

    @tornado.web.authenticated
    def get(self):
        self.check_admin()
        self.render('load.html', missing=[])

    @tornado.web.authenticated
    def post(self):
        self.check_admin()
        try:
            infiles = self.request.files.get('sebfile')
            if not infiles:
                raise ValueError('no file selected')
            infile = infiles[0]
            tmp = tempfile.NamedTemporaryFile(suffix='.xlsx')
            tmp.write(infile['body'])
            tmp.seek(0)
            wb = openpyxl.load_workbook(tmp.name)
            records = list(wb.active.values)
            datum_pos = 0
            for header_pos, header in enumerate(records):
                if header[datum_pos] == 'Datum':
                    break
            else:
                raise ValueError('could not find header in XLSX file')
            for pos, cell in enumerate(header):
                if cell == 'Belopp':
                    belopp_pos = pos
                    break
            else:
                raise ValueError("no column 'Belopp'")
            for pos, cell in enumerate(header):
                if cell == 'Text':
                    swish_pos = pos
                    break
            else:
                raise ValueError("no column 'Text'")
            payments = []
            missing = []
            for record in records[header_pos+1:]:
                swish = str(record[swish_pos])
                for prefix, replacement in settings['SWISH_NUMBER_PREFIXES'].items():
                    if swish.startswith(prefix):
                        swish = replacement + swish[len(prefix):]
                        break
                try:
                    member = self.get_member(swish)
                except KeyError:
                    missing.append(swish)
                else:
                    datum = record[datum_pos]
                    if isinstance(datum, datetime.datetime):
                        datum = datum.date().isoformat()
                    elif isinstance(datum, datetime.date):
                        datum = datum.isoformat()
                    else:
                        datum = str(datum)
                    payments.append({'member': member['email'],
                                     'lazy': settings['GLOBAL_SWISH_LAZY'] or
                                             member.get('swish_lazy'),
                                     'date': datum,
                                     'amount': float(record[belopp_pos])})
            if missing:
                raise ValueError('Some Swish numbers missing')
            for payment in payments:
                with EventSaver(rqh=self) as saver:
                    saver['member'] = payment['member']
                    saver.set_payment(payment='swish',
                                      amount=payment['amount'],
                                      date=payment['date'])
                if payment['lazy']:
                    with EventSaver(rqh=self) as saver:
                        saver['member'] = payment['member']
                        saver.set_purchase(purchase='credit',
                                           amount=payment['amount'],
                                           description='Swish lazy',
                                           date=payment['date'])
        except (IndexError, ValueError, IOError) as error:
            self.set_error_flash(str(error))
            self.render('load.html', missing=missing)
        else:
            self.see_other('ledger')

class Expenditure(RequestHandler):
    "Expenditure that reduces the credit of the BeerClub master virtual member."

    @tornado.web.authenticated
    def get(self):
        self.check_admin()
        self.render('expenditure.html')

    @tornado.web.authenticated
    def post(self):
        self.check_admin()
        try:
            with EventSaver(rqh=self) as saver:
                saver['member'] = constants.BEERCLUB
                saver.set_payment(
                    payment=constants.EXPENDITURE,
                    amount=self.get_argument('amount', None),
                    description=self.get_argument('description', None),
                    date=self.get_argument('date', utils.today()))
        except ValueError as error:
            self.set_error_flash(str(error))
        self.see_other('payments')


class Cash(RequestHandler):
    """Cash transfer from cash box via some admin.
    Increases the credit of the BeerClub master virtual member.
    """

    @tornado.web.authenticated
    def get(self):
        self.check_admin()
        self.render('cash.html')

    @tornado.web.authenticated
    def post(self):
        self.check_admin()
        try:
            with EventSaver(rqh=self) as saver:
                saver['member'] = constants.BEERCLUB
                saver.set_payment(
                    payment=constants.CASH,
                    amount=self.get_argument('amount', None),
                    date=self.get_argument('date', utils.today()))
        except ValueError as error:
            self.set_error_flash(str(error))
        self.see_other('payments')


class Account(RequestHandler):
    "View events for a member account."

    @tornado.web.authenticated
    def get(self, email):
        try:
            member = self.get_member(email, check=True)
        except KeyError:
            self.see_other('home')
            return 
        member['balance'] = self.get_balance(member)
        member['count'] = self.get_count(member)
        try:
            from_ = self.get_argument('from')
        except tornado.web.MissingArgumentError:
            from_ = utils.today(-settings['DISPLAY_ACCOUNT_DAYS'])
        try:
            to = self.get_argument('to')
        except tornado.web.MissingArgumentError:
            to = utils.today()
        if from_ > to:
            events = []
        else:
            events = self.get_docs('event/member',
                                   key=[member['email'], from_],
                                   last=[member['email'], to+constants.CEILING])
        self.render('account.html',
                    member=member, events=events, from_=from_, to=to)


class Activity(RequestHandler):
    "Members having made credit-affecting purchases recently."

    @tornado.web.authenticated
    def get(self):
        self.check_admin()
        activity = dict()
        from_ = utils.today(-settings['DISPLAY_ACTIVITY_DAYS'])
        to = utils.today()
        view = self.db.view('event/activity')
        for row in view[from_ : to+constants.CEILING]:
            try:
                activity[row.value] = max(activity[row.value], row.key)
            except KeyError:
                activity[row.value] = row.key
        activity.pop(constants.BEERCLUB, None)
        activity = list(activity.items())
        activity.sort(key=lambda i: i[1])
        # This is more efficient than calling for each member.
        all_members = self.get_docs('member/email')
        lookup = {}
        for member in all_members:
            lookup[member['email']] = member
        members = []
        for email, timestamp in activity:
            member = lookup[email]
            member['activity'] = timestamp
            members.append(member)
        utils.get_balances(self.db, members)
        self.render('activity.html', members=members)


class Ledger(RequestHandler):
    "Ledger page for listing recent events."

    @tornado.web.authenticated
    def get(self):
        "Display recent events."
        try:
            from_ = self.get_argument('from')
        except tornado.web.MissingArgumentError:
            from_ = utils.today(-settings['DISPLAY_LEDGER_DAYS'])
        try:
            to = self.get_argument('to')
        except tornado.web.MissingArgumentError:
            to = utils.today()
        if from_ > to:
            events = []
        else:
            events = self.get_docs('event/ledger',
                                   key=from_,
                                   last=to+constants.CEILING)
        self.render('ledger.html',
                    beerclub_balance=self.get_beerclub_balance(),
                    members_balance=self.get_balance(),
                    events=events,
                    from_=from_,
                    to=to)


class LedgerCsv(Ledger):
    "CSV output of ledger data."

    def render(self, template, events, from_, to, **kwargs):
        csvbuffer = StringIO()
        writer = csv.writer(csvbuffer)
        row = ['Action',
               'Id',
               'Member',
               'Beverage',
               'Description',
               'Credit',
               'Date',
               'Actor',
               'Timestamp']
        writer.writerow(row)
        for event in events:
            writer.writerow([event['action'],
                             event['_id'],
                             event['member'],
                             event.get('beverage') or '',
                             event.get('description') or '',
                             event['credit'],
                             event.get('date') or '',
                             event['log'].get('member') or '',
                             event['log']['timestamp']])
        self.write(csvbuffer.getvalue())
        self.set_header('Content-Type', constants.CSV_MIME)
        self.set_header('Content-Disposition', 
                        'attachment; filename="ledger.csv')


class Payments(RequestHandler):
    "Page for listing recent payment events, and the Beer Club balance."

    @tornado.web.authenticated
    def get(self):
        "Display recent payment events."
        try:
            from_ = self.get_argument('from')
        except tornado.web.MissingArgumentError:
            from_ = utils.today(-settings['DISPLAY_PAYMENT_DAYS'])
        try:
            to = self.get_argument('to')
        except tornado.web.MissingArgumentError:
            to = utils.today()
        if from_ > to:
            events = []
        else:
            events = self.get_docs('event/payment',
                                   key=from_,
                                   last=to+constants.CEILING)
        self.render('payments.html', events=events, from_=from_, to=to)


class PaymentsCsv(Payments):
    "CSV output of payment data."

    def render(self, template, events, from_, to, **kwargs):
        csvbuffer = StringIO()
        writer = csv.writer(csvbuffer)
        row = ['Id',
               'Member',
               'Description',
               'Credit',
               'Date',
               'Actor',
               'Timestamp']
        writer.writerow(row)
        for event in events:
            writer.writerow([event['_id'],
                             event['member'],
                             event.get('description') or '',
                             event['credit'],
                             event.get('date') or '',
                             event['log'].get('member') or '',
                             event['log']['timestamp']])
        self.write(csvbuffer.getvalue())
        self.set_header('Content-Type', constants.CSV_MIME)
        self.set_header('Content-Disposition', 
                        'attachment; filename="payments.csv')


class EventApiV1(ApiMixin, RequestHandler):
    "Return event data."

    @tornado.web.authenticated
    def get(self, iuid):
        self.check_admin()
        event = self.get_doc(iuid)
        if event.get(constants.DOCTYPE) != constants.EVENT:
            raise tornado.web.HTTPError(404, reason='no such event')
        data = dict(iuid=event['_id'])
        for key in ['action', 'beverage', 'credit',
                    'date', 'description', 'log']:
            data[key] = event.get(key)
        self.write(data)


class MemberEventApiV1(ApiMixin, RequestHandler):
    "Add an event for the member."

    @tornado.web.authenticated
    def post(self, email):
        self.check_admin()
        try:
            member = self.get_member(email)
        except KeyError:
            raise tornado.web.HTTPError(404, reason='no such member')
        try:
            with EventSaver(rqh=self) as saver:
                saver['member'] = member['email']
                saver.set(self.get_json_body())
        except ValueError as error:
            raise tornado.web.HTTPError(400, reason=str(error))
        self.write(dict(iuid=saver.doc['_id']))
