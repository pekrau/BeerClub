"Member account handling; member of Beer Club."

import csv
import logging
import fnmatch
from io import StringIO

import tornado.web

from beerclub import constants
from beerclub import settings
from beerclub import utils
from beerclub.requesthandler import RequestHandler, ApiMixin
from beerclub.saver import Saver

EMAIL_SENT = 'An email with instructions has been sent.'
PENDING_MESSAGE = 'An administrator will inspect your registration.' \
                  ' An email will be sent if your member account is enabled.'

PENDING_SUBJECT = "A {site} member account {email} is pending"
PENDING_TEXT = """A {site} member account {email} is pending.

Inspect the member account at {url} and enable or disable.
"""

RESET_SUBJECT = "Your {site} member account password has been reset."
RESET_TEXT = """Your {site} member account {email} password has been reset.

To set a new password, go to {url}. 

This unique link contains a code allowing you to set the password.

Please also check and correct your settings.

Yours,
The {site} administrators
"""

ENABLED_SUBJECT = "Your {site} member account has been enabled"
ENABLED_TEXT = """Your {site} member account {email} has been enabled.

You need to set the password for it. Go to {url}.

This unique link contains a code allowing you to set the password.

Yours,
The {site} administrators
"""


class MemberSaver(Saver):
    doctype = constants.MEMBER

    def initialize(self):
        self['status'] = constants.PENDING
        self['password'] = None

    def set_name(self):
        try:
            self['first_name'] = self.rqh.get_argument('first_name')
            self['last_name'] = self.rqh.get_argument('last_name')
        except tornado.web.MissingArgumentError:
            raise ValueError('Missing first or last name.')

    def set_swish(self):
        try:
            swish = self.rqh.get_argument('swish')
            if swish:
                swish = utils.normalize_swish(swish)
                try:
                    other = self.rqh.get_member(swish)
                except KeyError:
                    pass
                else:
                    if other['email'] != self.doc['email']:
                        raise ValueError('Swish number is already in use.')
            self['swish'] = swish or None
        except tornado.web.MissingArgumentError:
            self['swish'] = None
        lazy = self.rqh.get_argument('swish_lazy', False)
        self['swish_lazy'] = lazy and lazy.lower() == 'true'

    def set_address(self):
        self['address'] = self.rqh.get_argument('address', None) or None

    def set_api_key(self):
        if not self.rqh.is_admin(): return
        if self['role'] != constants.ADMIN: return
        try:
            if self.rqh.get_argument('api_key', False):
                self['api_key'] = utils.get_iuid()
        except (tornado.web.MissingArgumentError, ValueError):
            pass

    def set_role(self):
        if not self.rqh.is_admin(): return
        if self.rqh.current_user['email'] == self['email']: return
        try:
            role = self.rqh.get_argument('role')
            if role not in constants.ROLES: raise ValueError
            self['role'] = role
        except (tornado.web.MissingArgumentError, ValueError):
            pass


class Member(RequestHandler):
    "View a member account."

    def no_events(self, member):
        "Are there no events for the member?"
        events = self.get_docs('event/member',            
                               key=[member['email'], constants.CEILING],
                               last=[member['email'], ''],
                               descending=True,
                               limit=1)
        return len(events) == 0

    @tornado.web.authenticated
    def get(self, email):
        try:
            member = self.get_member(email, check=True)
        except KeyError:
            self.see_other('home')
        else:
            member['balance'] = self.get_balance(member)
            deletable = self.no_events(member) and \
                        member['role'] != constants.ADMIN
            self.render('member.html', member=member, deletable=deletable)

    @tornado.web.authenticated
    def post(self, email):
        "Delete this member; only if has no events and is not admin."
        self.check_admin()
        try:
            member = self.get_member(email, check=True)
        except KeyError:
            self.see_other('home')
            return
        if self.get_argument('_http_method', None) == 'DELETE' and \
           self.no_events(member) and member['role'] != constants.ADMIN:
            self.db.delete(member)
        url = self.get_argument('next', None)
        if url:
            self.redirect(url)
        else:
            self.see_other('home')


class Settings(RequestHandler):
    "Edit a member account; change values, enable or disable."

    @tornado.web.authenticated
    def get(self, email):
        try:
            member = self.get_member(email, check=True)
        except KeyError:
            self.see_other('home')
        else:
            self.render('settings.html', member=member)

    @tornado.web.authenticated
    def post(self, email):
        try:
            member = self.get_member(email, check=True)
        except KeyError:
            self.see_other('home')
            return
        try:
            with MemberSaver(doc=member, rqh=self) as saver:
                saver.set_name()
                saver.set_swish()
                saver.set_address()
                saver.set_api_key()
                saver.set_role()
        except ValueError as error:
            self.set_error_flash(str(error))
            self.see_other('settings', member['email'])
            return
        if self.is_admin():
            self.see_other('member', member['email'])
        else:
            self.see_other('home')


class Members(RequestHandler):
    "View a table of all member accounts."

    @tornado.web.authenticated
    def get(self):
        self.check_admin()
        members = self.get_docs('member/email')
        utils.get_balances(self.db, members)
        self.render('members.html', members=members)


class MembersCsv(Members):
    "CSV output of members accounts."

    def render(self, template, members):
        csvbuffer = StringIO()
        writer = csv.writer(csvbuffer)
        row = ['Member',
               'First name',
               'Last name',
               'Balance',
               'Role',
               'Status',
               'Last login']
        if settings['MEMBER_SWISH']:
            row.extend(['Swish', 'Swish lazy'])
        if settings['MEMBER_ADDRESS']:
            row.append('Address')
        writer.writerow(row)
        for member in members:
            row = [member['email'],
                   member['first_name'],
                   member['last_name'],
                   member['balance'],
                   member['role'],
                   member['status'],
                   member.get('last_login') or '']
            if settings['MEMBER_SWISH']:
                row.extend([member.get('swish') or '',
                            member.get('swish_lazy') or ''])
            if settings['MEMBER_ADDRESS']:
                row.append(member.get('address') or '')
            writer.writerow(row)
        self.write(csvbuffer.getvalue())
        self.set_header('Content-Type', constants.CSV_MIME)
        self.set_header('Content-Disposition', 
                        'attachment; filename="members.csv"')


class Pending(RequestHandler):
    "View a table of pending member accounts."

    @tornado.web.authenticated
    def get(self):
        self.check_admin()
        members = self.get_docs('member/status', key=constants.PENDING)
        members.sort(key=lambda m: m['email'])
        self.render('pending.html', members=members)


class Login(RequestHandler):
    "Login resource."

    def post(self):
        "Login to a member account. Set a secure cookie."
        try:
            email = self.get_argument('email').lower()
            password = self.get_argument('password')
        except tornado.web.MissingArgumentError:
            self.set_error_flash('Missing email or password argument.')
            self.see_other('home')
            return
        try:
            member = self.get_member(email)
            if member['status'] == constants.DISABLED:
                raise ValueError
            if utils.hashed_password(password) != member.get('password'):
                raise KeyError
        except KeyError:
            self.set_error_flash('No such member or invalid password.')
        except ValueError:
            self.set_error_flash("Your member account is disabled."
                                 " Contact the %s administrators."
                                 % settings['SITE_NAME'])
        else:
            with MemberSaver(doc=member, rqh=self) as saver:
                saver['login']      = utils.timestamp() # Set login session.
                saver['last_login'] = saver['login']    # Set last login.
            logging.info("Login auth: %s", member['email'])
            self.set_secure_cookie(constants.USER_COOKIE,
                                   member['email'],
                                   expires_days=settings['LOGIN_SESSION_DAYS'])
        self.see_other('home')


class Logout(RequestHandler):
    "Logout; unset the secure cookie, and invalidate login session."

    @tornado.web.authenticated
    def post(self):
        with MemberSaver(doc=self.current_user, rqh=self) as saver:
            saver['login'] = None  # Unset login session.
        self.set_secure_cookie(constants.USER_COOKIE, '')
        self.see_other('home')


class Reset(RequestHandler):
    "Reset the password of a member account."

    def post(self):
        try:
            member = self.get_member(self.get_argument('email'))
        except (tornado.web.MissingArgumentError, KeyError):
            self.see_other('home', error='No such member account.')
        else:
            if member.get('status') == constants.PENDING:
                self.see_other('home', error='Cannot reset password.'
                               ' Member account has not been enabled.')
                return
            elif member.get('status') == constants.DISABLED:
                self.see_other('home', error='Cannot reset password.'
                               ' Member account is disabled.')
                return
            with MemberSaver(doc=member, rqh=self) as saver:
                saver['password'] = None
                saver['code']     = utils.get_iuid()
            data = dict(email=member['email'],
                        site=settings['SITE_NAME'],
                        url = self.absolute_reverse_url('password',
                                                    email=member['email'],
                                                    code=member['code']))
            email_server = utils.EmailServer()
            email_server.send(member['email'],
                              RESET_SUBJECT.format(**data),
                              RESET_TEXT.format(**data))
            if self.current_user and not self.is_admin():
                # Log out the user if not admin
                self.set_secure_cookie(constants.USER_COOKIE, '')
            self.see_other('home', message=EMAIL_SENT)


class Password(RequestHandler):
    "Set the password of a member account; requires a code."

    def get(self):
        self.render('password.html',
                    email=self.get_argument('email', default=''),
                    code=self.get_argument('code', default=''))

    def post(self):
        try:
            member = self.get_member(self.get_argument('email'))
            if member.get('code') != self.get_argument('code'):
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
                raise ValueError('The password is too short.')
        except ValueError as msg:
            self.see_other('password',
                           email=self.get_argument('email') or '',
                           code=self.get_argument('code') or '',
                           error=str(msg))
            return 
        with MemberSaver(doc=member, rqh=self) as saver:
            saver['password'] = utils.hashed_password(password)
            saver['login'] = utils.timestamp()     # Set login session.
            saver['last_login'] = saver['login']   # Set last login.
            saver['code'] = None
        self.set_secure_cookie(constants.USER_COOKIE,
                               member['email'],
                               expires_days=settings['LOGIN_SESSION_DAYS'])
        self.see_other('home')


class Register(RequestHandler):
    "Register a member account."

    @tornado.web.authenticated
    def get(self):
        "Register a member. Only admin should be able to register someone else."
        self.check_admin()
        self.render('register.html')

    def post(self):
        try:
            with MemberSaver(rqh=self) as saver:
                try:
                    email = self.get_argument('email').lower()
                    if not email: raise ValueError
                except (tornado.web.MissingArgumentError, ValueError):
                    raise ValueError('No email address provided.')
                if not fnmatch.fnmatch(email, constants.EMAIL_PATTERN):
                    raise ValueError('Invalid email address provided.')
                try:
                    member = self.get_doc(email, 'member/email')
                except KeyError:
                    pass
                else:
                    raise ValueError('Member account exists!'
                                     ' Please use Reset password.')
                saver['email']   = email
                saver.set_name()
                saver.set_swish()
                saver.set_address()
                # Set the very first member account in the database
                # to be admin and enabled.
                count = len(self.get_docs('member/email', key='',
                                          last=constants.CEILING, limit=2))
                if count == 0:
                    saver['role'] = constants.ADMIN
                    saver['status'] = constants.ENABLED
                    saver['code'] = code = utils.get_iuid()
                else:
                    saver['role'] = constants.MEMBER
                ptn = settings['MEMBER_EMAIL_AUTOENABLE']
                # Enable directly if pattern match.
                if ptn and fnmatch.fnmatch(saver['email'], ptn):
                    saver['status'] = constants.ENABLED
                    saver['code'] = code = utils.get_iuid()
        except ValueError as error:
            self.set_message_flash(str(error))
            self.see_other('home')
            return
        member = saver.doc
        data = dict(email=member['email'], site=settings['SITE_NAME'])
        email_server = utils.EmailServer()
        if member['status'] == constants.ENABLED:
            data['url'] = self.absolute_reverse_url('password',
                                                    email=email,
                                                    code=code)
            email_server.send(member['email'],
                              ENABLED_SUBJECT.format(**data),
                              ENABLED_TEXT.format(**data))
            self.set_message_flash(EMAIL_SENT)
        else:
            data['url'] = self.absolute_reverse_url('member', data['email'])
            subject = PENDING_SUBJECT.format(**data)
            text = PENDING_TEXT.format(**data)
            for admin in self.get_docs('member/role', key=constants.ADMIN):
                email_server.send(admin['email'], subject, text)
            self.set_message_flash(PENDING_MESSAGE)
        if self.is_admin():
            self.see_other('member', member['email'])
        else:
            self.see_other('home')


class Enable(RequestHandler):
    "Enable a member account."

    @tornado.web.authenticated
    def post(self, email):
        self.check_admin()
        member = self.get_member(email)
        with MemberSaver(doc=member, rqh=self) as saver:
            saver['status']   = constants.ENABLED
            saver['login']    = None
            saver['password'] = None
            saver['code']     = utils.get_iuid()
        email_server = utils.EmailServer()
        data = dict(email=member['email'],
                    site=settings['SITE_NAME'],
                    url=self.absolute_reverse_url('password',
                                                  email=member['email'],
                                                  code=member['code']))
        email_server.send(member['email'],
                          ENABLED_SUBJECT.format(**data),
                          ENABLED_TEXT.format(**data))
        self.set_message_flash(EMAIL_SENT)
        url = self.get_argument('next', None)
        if url:
            self.redirect(url)
        else:
            self.see_other('member', member['email'])


class Disable(RequestHandler):
    "Disable a member account."

    @tornado.web.authenticated
    def post(self, email):
        self.check_admin()
        member = self.get_member(email)
        with MemberSaver(doc=member, rqh=self) as saver:
            saver['status']   = constants.DISABLED
            saver['login']    = None
            saver['password'] = None
            saver['code']     = None
        url = self.get_argument('next', None)
        if url:
            self.redirect(url)
        else:
            self.see_other('member', member['email'])


class MemberApiV1(ApiMixin, RequestHandler):
    "Get member data."

    @tornado.web.authenticated
    def get(self, email):
        self.check_admin()
        try:
            member = self.get_member(email)
        except KeyError:
            raise tornado.web.HTTPError(404, reason='no such member')
        data = {}
        for key in ['email', 'first_name', 'last_name', 'role', 'status']:
            data[key] = member.get(key)
        if settings['MEMBER_SWISH']:
            data['swish'] = member.get('swish')
            data['swish_lazy'] = member.get('swish_lazy')
        if settings['MEMBER_ADDRESS']:
            data['address'] = member.get('address')
        self.write(data)
