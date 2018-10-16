"RequestHandler subclass."

import base64
import logging
import urllib
from collections import OrderedDict as OD

import couchdb
import tornado.web

from . import constants
from . import settings
from . import utils


class RequestHandler(tornado.web.RequestHandler):
    "Base request handler."

    def prepare(self):
        "Get the database connection."
        server = couchdb.Server(settings['DATABASE_SERVER'])
        if settings.get('DATABASE_ACCOUNT') and settings.get('DATABASE_PASSWORD'):
            server.resource.credentials = (settings.get('DATABASE_ACCOUNT'),
                                           settings.get('DATABASE_PASSWORD'))
        try:
            self.db = server[settings['DATABASE_NAME']]
        except couchdb.http.ResourceNotFound:
            raise KeyError("CouchDB database '%s' does not exist." % 
                           settings['DATABASE_NAME'])

    def get_template_namespace(self):
        "Set the variables accessible within the template."
        result = super(RequestHandler, self).get_template_namespace()
        result['constants'] = constants
        result['settings'] = settings
        result['is_admin'] = self.is_admin()
        result['error'] = self.get_cookie('error', '').replace('_', ' ')
        self.clear_cookie('error')
        result['message'] = self.get_cookie('message', '').replace('_', ' ')
        self.clear_cookie('message')
        return result

    def see_other(self, name, *args, **kwargs):
        """Redirect to the absolute URL given by name
        using HTTP status 303 See Other."""
        query = kwargs.copy()
        try:
            self.set_error_flash(query.pop('error'))
        except KeyError:
            pass
        try:
            self.set_message_flash(query.pop('message'))
        except KeyError:
            pass
        url = self.absolute_reverse_url(name, *args, **query)
        self.redirect(url, status=303)

    def absolute_reverse_url(self, name, *args, **query):
        "Get the absolute URL given the handler name, arguments and query."
        if name is None:
            path = ''
        else:
            path = self.reverse_url(name, *args, **query)
        return settings['BASE_URL'].rstrip('/') + path

    def reverse_url(self, name, *args, **query):
        "Allow adding query arguments to the URL."
        url = super(RequestHandler, self).reverse_url(name, *args)
        url = url.rstrip('?')   # tornado bug? sometimes left-over '?'
        if query:
            query = dict([(k, utils.to_utf8(v)) for k,v in query.items()])
            url += '?' + urllib.urlencode(query)
        return url

    def set_message_flash(self, message):
        "Set message flash cookie."
        self.set_flash('message', message)

    def set_error_flash(self, message):
        "Set error flash cookie message."
        self.set_flash('error', message)

    def set_flash(self, name, message):
        message = message.replace(' ', '_')
        message = message.replace(';', '_')
        message = message.replace(',', '_')
        self.set_cookie(name, message)

    def get_doc(self, key, viewname=None):
        """Get the document with the given id, or from the given view.
        Raise KeyError if not found.
        """
        return utils.get_doc(self.db, key, viewname=viewname)

    def get_docs(self, viewname, key=None, last=None, **kwargs):
        """Get the list of documents using the named view
        and the given key or interval.
        """
        return utils.get_docs(self.db, viewname, key=key, last=last, **kwargs)

    def get_account(self, email, check=False):
        """Get the account identified by the email address.
        Raise KeyError if no such account or if not allowed to view it.
        """
        try:
            account = utils.get_account(self.db, email)
        except KeyError:
            self.set_error_message('No such account.')
            raise KeyError
        if check:
            if not (self.is_admin() or 
                    account['email'] == self.current_user['email']):
                self.set_error_message('You may not view the account.')
                raise KeyError
        return account

    def get_credit(self, account=None):
        "Get the current credit status for the account."
        if account is None:
            account = self.current_user
        result = list(self.db.view('event/credit',
                                   key=account['email'],
                                   group_level=1,
                                   reduce=True))
        if result:
            return result[0].value
        else:
            return 0

    def get_beverages_count(self, account=None, date=utils.today()):
        "Get the number of beverages purchased on the given date."
        if account is None:
            account = self.current_user
        result = list(self.db.view('event/beverages',
                                   key=[account['email'], date],
                                   group_level=2,
                                   reduce=True))
        if result:
            return result[0].value
        else:
            return 0

    def get_current_user(self):
        """Get the currently logged-in user account, or None.
        This overrides a tornado function, otherwise it should have
        been called 'get_current_account', since the term 'account'
        is used in this code rather than 'user'."""
        try:
            return self.get_current_user_session()
        except ValueError:
            try:
                return self.get_current_user_basic()
            except ValueError:
                pass
        return None

    def get_current_user_session(self):
        """Get the current user from a secure login session cookie.
        Raise ValueError if no or erroneous authentication.
        """
        email = self.get_secure_cookie(
            constants.USER_COOKIE,
            max_age_days=settings['LOGIN_MAX_AGE_DAYS'])
        if not email: raise ValueError
        try:
            account = self.get_account(email)
        except KeyError:
            return None
        # Disabled; must not be allowed to login.
        if account.get('disabled'):
            logging.info("Session auth: DISABLED %s", account['email'])
            return None
        else:
            # Check if valid login session.
            if account.get('login') is None: raise ValueError
            # All fine.
            logging.info("Session auth: %s", account['email'])
            return account

    def get_current_user_basic(self):
        """Get the current user by HTTP Basic authentication.
        This should be used only if the site is using TLS (SSL, https).
        Raise ValueError if no or erroneous authentication.
        """
        try:
            auth = self.request.headers['Authorization']
        except KeyError:
            raise ValueError
        try:
            auth = auth.split()
            if auth[0].lower() != 'basic': raise ValueError
            auth = base64.b64decode(auth[1])
            email, password = auth.split(':', 1)
            account = self.get_account(email)
            if utils.hashed_password(password) != account.get('password'):
                raise ValueError
        except (IndexError, ValueError, TypeError):
            raise ValueError
        if account.get('disabled'):
            logging.info("Basic auth login: DISABLED %s", account['email'])
            return None
        else:
            logging.info("Basic auth login: %s", account['email'])
            return account

    def is_admin(self):
        "Is the current user an administrator?"
        if not self.current_user: return False
        return self.current_user['role'] == constants.ADMIN

    def check_admin(self):
        "Check that the current user is an administrator."
        if not self.is_admin():
            raise tornado.web.HTTPError(403, reason="Role 'admin' is required")
