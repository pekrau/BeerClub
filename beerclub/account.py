"Account handling; member of Beer Club."

import logging
import fnmatch

import tornado.web

from . import constants
from . import utils
from .requesthandler import RequestHandler
from .saver import Saver


class AccountSaver(Saver):
    doctype = constants.ACCOUNT

    def initialize(self):
        self['status'] = constants.PENDING
        self['password'] = None


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
            self.set_secure_cookie(constants.USER_COOKIE,
                                   account['email'],
                                   expires_days=settings['LOGIN_MAX_AGE_DAYS'])
            self.redirect(self.get_argument('next', self.reverse_url('home')))


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
        with AccountSaver(rqh=self) as saver:
            for key in keys:
                saver[key] = data[key]
            pattern = settings['ACCOUNT_EMAIL_AUTOENABLE']
            if pattern and fnmatch.fnmatch(account['email'], pattern):
                saver['status'] = constants.ENABLED
        account = saver.doc
        if account['status'] == constants.ENABLED:
            # Send email if enabled
            pass
        else:
            # Else send email to admins
            pass
        self.redirect(self.reverse_url('home'))
