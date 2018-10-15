"Account handling; member of Beer Club."

import logging
import fnmatch

import tornado.web

from . import constants
from . import settings
from . import utils
from .requesthandler import RequestHandler
from .saver import Saver

PENDING_SUBJECT = "Your {site} account {email} is pending"
PENDING_TEXT = """Your {site} account {email} is pending.

A {site} administrator will inspect your account. You will receive
an email with instructions when the account has been enabled.

Yours,
The {site} administrators
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
        raise NotImplementedError


class AccountEdit(RequestHandler):
    "Edit an account."

    @tornado.web.authenticated
    def get(self, email):
        raise NotImplementedError


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
            if utils.hashed_password(password) != account.get('password'):
                raise KeyError
        except KeyError:
            self.set_error_flash('No such account or invalid password.')
            self.see_other('home')
        else:
            with AccountSaver(doc=account, rqh=self) as saver:
                saver['login'] = utils.timestamp()     # Set login session.
                saver['latest_login'] = saver['login'] # Set latest login.
            self.set_secure_cookie(constants.USER_COOKIE,
                                   account['email'],
                                   expires_days=settings['LOGIN_MAX_AGE_DAYS'])
            self.redirect(self.reverse_url('home'))


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
        except (tornado.web.MissingArgumentError, ValueError):
            self.see_other('home') # Silent error! Should not show existence.
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
            self.see_other('home',
                           message="An email has been sent containing"
                           " a reset code. Please wait a couple of"
                           " minutes for it and use the link in it.")


class Password(RequestHandler):
    "Set the password of a account account; requires a code."

    def get(self):
        self.render('password.html',
                    email=self.get_argument('email', default=''),
                    code=self.get_argument('code', default=''))

    def post(self):
        try:
            account = self.get_account(self.get_argument('email', ''))
            if account.get('code') != self.get_argument('code', ''):
                raise ValueError
        except (KeyError, ValueError):
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
            saver['login'] = utils.timestamp() # Set latest login.
            saver['code'] = None
        self.set_secure_cookie(constants.USER_COOKIE,
                               account['email'],
                               expires_days=settings['LOGIN_MAX_AGE_DAYS'])
        self.see_other('home')


class Register(RequestHandler):
    "Register an account."

    def post(self):
        data = {}
        keys = ['email', 'name', 'phone', 'address']
        for key in keys:
            try:
                data[key] = self.get_argument('email')
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
            for key in keys:
                saver[key] = data[key]
            # Set first account to be admin.
            count = len(self.get_docs('account/email', key='',
                                      last=constants.CEILING, limit=2))
            if count == 0:
                saver['role'] = constants.ADMIN
            else:
                saver['role'] = constants.MEMBER
            ptn = settings['ACCOUNT_EMAIL_AUTOENABLE']
            if count or (ptn and fnmatch.fnmatch(saver['email'], ptn)):
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
            self.set_message_flash('An email with instructions has been sent.')
        else:
            data['url'] = self.absolute_reverse_url('account_edit',
                                                    data['email'])
            subject = PENDING_SUBJECT.format(**data)
            text = PENDING_TEXT.format(**data)
            for admin in self.get_docs(constants.ADMIN, 'account/role'):
                email_server.send(admin['email'], subject, text)
            self.set_message_flash('Please wait until your account'
                                   ' has been enabled by an administrator.')
        self.redirect(self.reverse_url('home'))


class Enable(RequestHandler):
    "Enable an account."

    @tornado.web.authenticated
    def post(self, email):
        self.check_admin()
        account = self.get_account(email)
        with AccountSaver(doc=account, rqh=self) as saver:
            saver['status'] = constants.ENABLED
            saver['login'] = None
            saver['code'] = utils.get_iuid()
        self.see_other('account', account['email'])
        email_server = utils.EmailServer()
        data = dict(site=settings['SITE_NAME'],
                    url=self.absolute_reverse_url('password',
                                                  email=data['email'],
                                                  code=data['code']))
        email_server.send(account['email'],
                          ENABLED_SUBJECT.format(**data),
                          ENABLED_TEXT.format(**data))
        self.set_message_flash('An email with instructions has been sent.')


class Disable(RequestHandler):
    "Disable an account."

    @tornado.web.authenticated
    def post(self, email):
        self.check_admin()
        account = self.get_account(email)
        with AccountSaver(doc=account, rqh=self) as saver:
            saver['status'] = constants.DISABLED
            saver['login'] = None
            saver['code'] = None
        self.see_other('account', account['email'])
