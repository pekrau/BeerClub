"Account handling; member of Beer Club."

import logging
import fnmatch

import tornado.web

from . import constants
from . import settings
from . import utils
from .requesthandler import RequestHandler
from .saver import Saver

EMAIL_SENT = 'An email with instructions has been sent.'
PENDING_MESSAGE = 'An administrator will inspect your account.' \
                  ' An email will be sent if the account is enabled.'

PENDING_SUBJECT = "A {site} account {email} is pending"
PENDING_TEXT = """A {site} account {email} is pending.

Inspect the account at {url} and enable or disable.
"""

RESET_SUBJECT = "Your {site} account has been reset."
RESET_TEXT = """Your {site} account {email} has been reset.

To set its password, go to {url}. This link contains a
one-time code allowing you to set the password.

Yours,
The {site} administrators
"""

ENABLED_SUBJECT = "Your {site} account enabled"
ENABLED_TEXT = """Your {site} account {email} has been enabled.

You need to set the password for it. Go to {url}. This link contains a
one-time code allowing you to set the password.

Yours,
The {site} administrators
"""


class AccountSaver(Saver):
    doctype = constants.ACCOUNT

    def initialize(self):
        self['status'] = constants.PENDING
        self['password'] = None


class Account(RequestHandler):
    "View an account."

    @tornado.web.authenticated
    def get(self, email):
        try:
            account = self.get_account(email, check=True)
        except KeyError:
            self.see_other('home')
        else:
            self.render('account.html', account=account)


class AccountEdit(RequestHandler):
    "Edit an account; change values, enable or disable."

    @tornado.web.authenticated
    def get(self, email):
        try:
            account = self.get_account(email, check=True)
        except KeyError:
            self.see_other('home')
        else:
            self.render('account_edit.html', account=account)

    @tornado.web.authenticated
    def post(self, email):
        try:
            account = self.get_account(email, check=True)
        except KeyError:
            self.see_other('home')
            return
        data = {}
        for key in ['name', 'phone', 'address']:
            try:
                data[key] = self.get_argument(key)
            except tornado.web.MissingArgumentError:
                self.set_error_flash("No %s provided." % key)
                self.see_other('home')
                return
        role = None
        if self.is_admin() and self.current_user['email'] != email:
            try:
                role = self.get_argument('role')
                if role not in constants.ROLES: raise ValueError
            except (tornado.web.MissingArgumentError, ValueError):
                pass
        with AccountSaver(doc=account, rqh=self) as saver:
            saver['name'] = data['name']
            saver['phone'] = utils.normalize_phone(data['phone'])
            saver['address'] = data['address']
            if role:
                saver['role'] = role
        self.see_other('account', account['email'])


class Accounts(RequestHandler):
    "View a table of all accounts."

    @tornado.web.authenticated
    def get(self):
        self.check_admin()
        accounts = self.get_docs('account/email', key='',last=constants.CEILING)
        self.render('accounts.html', accounts=accounts)




class AccountHistory(RequestHandler):
    "View event history for an account."

    def initialize(self, all):
        self.all = all

    @tornado.web.authenticated
    def get(self, email):
        try:
            account = self.get_account(email, check=True)
        except KeyError:
            self.see_other('home')
            return 
        if self.all:
            kwargs = dict()
        else:
            kwargs = dict(limit=settings['DISPLAY_MAX_HISTORY'])
        events = self.get_docs('event/account',
                               key=[account['email'], constants.CEILING],
                               last=[account['email'], ''],
                               descending=True,
                               **kwargs)
        self.render('history.html',
                    account=account,
                    events=events, 
                    all=self.all)


class Login(RequestHandler):
    "Login resource."

    def post(self):
        "Login to a account account. Set a secure cookie."
        try:
            email = self.get_argument('email')
            password = self.get_argument('password')
        except tornado.web.MissingArgumentError:
            self.set_error_flash('Missing email or password argument.')
            self.see_other('home')
            return
        try:
            account = self.get_account(email)
            if account['status'] == constants.DISABLED:
                raise ValueError
            if utils.hashed_password(password) != account.get('password'):
                raise KeyError
        except KeyError:
            self.set_error_flash('No such account or invalid password.')
        except ValueError:
            self.set_error_flash("Your account is disabled."
                                 " Contact the %s administrators."
                                 % settings['SITE_NAME'])
        else:
            with AccountSaver(doc=account, rqh=self) as saver:
                saver['login'] = utils.timestamp()     # Set login session.
                saver['last_login'] = saver['login']   # Set last login.
            logging.info("Login auth: %s", account['email'])
            self.set_secure_cookie(constants.USER_COOKIE,
                                   account['email'],
                                   expires_days=settings['LOGIN_MAX_AGE_DAYS'])
        self.see_other('home')


class Logout(RequestHandler):
    "Logout; unset the secure cookie, and invalidate login session."

    @tornado.web.authenticated
    def post(self):
        with AccountSaver(doc=self.current_user, rqh=self) as saver:
            saver['login'] = None  # Unset login session.
        self.set_secure_cookie(constants.USER_COOKIE, '')
        self.see_other('home')


class Reset(RequestHandler):
    "Reset the password of a account account."

    def post(self):
        URL = self.absolute_reverse_url
        try:
            account = self.get_account(self.get_argument('email'))
        except (tornado.web.MissingArgumentError, KeyError):
            self.see_other('home') # Silent error.
        else:
            if account.get('status') == constants.PENDING:
                self.see_other('home', error='Cannot reset password.'
                               ' Account has not been enabled.')
                return
            elif account.get('status') == constants.DISABLED:
                self.see_other('home', error='Cannot reset password.'
                               ' Account is disabled; contact the site admin.')
                return
            with AccountSaver(doc=account, rqh=self) as saver:
                saver['password'] = None
                saver['code'] = utils.get_iuid()
            data = dict(email=account['email'],
                        site=settings['SITE_NAME'],
                        url = self.absolute_reverse_url('password',
                                                    email=account['email'],
                                                    code=account['code']))
            email_server = utils.EmailServer()
            email_server.send(account['email'],
                              RESET_SUBJECT.format(**data),
                              RESET_TEXT.format(**data))
            if self.current_user and not self.is_admin():
                # Log out the user if not admin
                self.set_secure_cookie(constants.USER_COOKIE, '')
            self.see_other('home', message=EMAIL_SENT)


class Password(RequestHandler):
    "Set the password of a account account; requires a code."

    def get(self):
        self.render('password.html',
                    email=self.get_argument('email', default=''),
                    code=self.get_argument('code', default=''))

    def post(self):
        try:
            account = self.get_account(self.get_argument('email'))
            if account.get('code') != self.get_argument('code'):
                raise ValueError
        except (tornado.web.MissingArgumentError, KeyError, ValueError):
            self.see_other('home',
                           error="Either the email address or the code" +
                           " for setting password was wrong." +
                           " Try doing 'Reset' again.")
            return
        password = self.get_argument('password', '')
        try:
            if len(password) < settings['MIN_PASSWORD_LENGTH']:
                raise ValueError('password is too short')
        except ValueError, msg:
            self.see_other('password',
                           email=self.get_argument('email') or '',
                           code=self.get_argument('code') or '',
                           error=str(msg))
            return 
        with AccountSaver(doc=account, rqh=self) as saver:
            saver['password'] = utils.hashed_password(password)
            saver['login'] = utils.timestamp()     # Set login session.
            saver['last_login'] = saver['login']   # Set last login.
            saver['code'] = None
        self.set_secure_cookie(constants.USER_COOKIE,
                               account['email'],
                               expires_days=settings['LOGIN_MAX_AGE_DAYS'])
        self.see_other('home')


class Register(RequestHandler):
    "Register an account."

    def post(self):
        data = {}
        for key in ['email', 'name', 'phone', 'address']:
            try:
                data[key] = self.get_argument(key)
            except tornado.web.MissingArgumentError:
                self.set_error_flash("No %s provided." % key)
                self.see_other('home')
                return
        if not fnmatch.fnmatch(data['email'], constants.EMAIL_PATTERN):
            self.set_error_flash('Invalid email provided.')
            self.see_other('home')
            return
        try:
            account = self.get_doc(data['email'], 'account/email')
        except KeyError:
            pass
        else:
            self.set_message_flash('Account already exists, use Reset.')
            self.see_other('home')
            return
        with AccountSaver(rqh=self) as saver:
            saver['email'] = data['email']
            saver['name'] = data['name']
            saver['phone'] = utils.normalize_phone(data['phone'])
            saver['address'] = data['address']
            # Set the very first account to be admin.
            count = len(self.get_docs('account/email', key='',
                                      last=constants.CEILING, limit=2))
            if count == 0:
                saver['role'] = constants.ADMIN
            else:
                saver['role'] = constants.MEMBER
            ptn = settings['ACCOUNT_EMAIL_AUTOENABLE']
            # First account, or pattern match, will be enabled directly.
            if count == 0 or (ptn and fnmatch.fnmatch(saver['email'], ptn)):
                saver['status'] = constants.ENABLED
                saver['code'] = data['code'] = utils.get_iuid()
        account = saver.doc
        data['site'] = settings['SITE_NAME']
        email_server = utils.EmailServer()
        if account['status'] == constants.ENABLED:
            data['url'] = self.absolute_reverse_url('password',
                                                    email=data['email'],
                                                    code=data['code'])
            email_server.send(account['email'],
                              ENABLED_SUBJECT.format(**data),
                              ENABLED_TEXT.format(**data))
            self.set_message_flash(EMAIL_SENT)
        else:
            data['url'] = self.absolute_reverse_url('account', data['email'])
            subject = PENDING_SUBJECT.format(**data)
            text = PENDING_TEXT.format(**data)
            for admin in self.get_docs('account/role', key=constants.ADMIN):
                email_server.send(admin['email'], subject, text)
            self.set_message_flash(PENDING_MESSAGE)
        self.see_other('home')


class Enable(RequestHandler):
    "Enable an account."

    @tornado.web.authenticated
    def post(self, email):
        self.check_admin()
        account = self.get_account(email)
        with AccountSaver(doc=account, rqh=self) as saver:
            saver['status'] = constants.ENABLED
            saver['login'] = None
            saver['password'] = None
            saver['code'] = utils.get_iuid()
        email_server = utils.EmailServer()
        data = dict(email=account['email'],
                    site=settings['SITE_NAME'],
                    url=self.absolute_reverse_url('password',
                                                  email=account['email'],
                                                  code=account['code']))
        email_server.send(account['email'],
                          ENABLED_SUBJECT.format(**data),
                          ENABLED_TEXT.format(**data))
        self.set_message_flash(EMAIL_SENT)
        self.see_other('account', account['email'])


class Disable(RequestHandler):
    "Disable an account."

    @tornado.web.authenticated
    def post(self, email):
        self.check_admin()
        account = self.get_account(email)
        with AccountSaver(doc=account, rqh=self) as saver:
            saver['status'] = constants.DISABLED
            saver['login'] = None
            saver['password'] = None
            saver['code'] = None
        self.see_other('account', account['email'])
