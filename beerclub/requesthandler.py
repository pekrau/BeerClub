"RequestHandler subclass."

from __future__ import print_function

import base64
import json
import logging
import urllib
from collections import OrderedDict as OD

import couchdb
import tornado.web

from . import settings


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
        result['settings'] = settings
        return result

    def see_other(self, name, *args, **query):
        """Redirect to the absolute URL given by name
        using HTTP status 303 See Other."""
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

    # def get_account(self, email):
    #     """Get the account identified by the email address.
    #     Raise KeyError if no such account.
    #     """
    #     return utils.get_account(self.db, email)

    # def get_current_user(self):
    #     """Get the currently logged-in user account, or None.
    #     This overrides a tornado function, otherwise it should have
    #     been called 'get_current_account', since the term 'account'
    #     is used in this code rather than 'user'."""
    #     try:
    #         return self.get_current_user_api_key()
    #     except ValueError:
    #         try:
    #             return self.get_current_user_session()
    #         except ValueError:
    #             try:
    #                 return self.get_current_user_basic()
    #             except ValueError:
    #                 pass
    #     return None

    # def get_current_user_api_key(self):
    #     """Get the current user by API key authentication.
    #     Raise ValueError if no or erroneous authentication.
    #     """
    #     try:
    #         api_key = self.request.headers[constants.API_KEY_HEADER]
    #     except KeyError:
    #         raise ValueError
    #     else:
    #         try:
    #             account = self.get_doc(api_key, 'account/api_key')
    #         except tornado.web.HTTPError:
    #             raise ValueError
    #         if account.get('disabled'):
    #             logging.info("API key login: DISABLED %s",
    #                          account['email'])
    #             return None
    #         else:
    #             logging.info("API key login: %s", account['email'])
    #             return account

    # def get_current_user_session(self):
    #     """Get the current user from a secure login session cookie.
    #     Raise ValueError if no or erroneous authentication.
    #     """
    #     email = self.get_secure_cookie(
    #         constants.USER_COOKIE,
    #         max_age_days=settings['LOGIN_MAX_AGE_DAYS'])
    #     if not email: raise ValueError
    #     try:
    #         account = self.get_account(email)
    #     except KeyError:
    #         return None
    #     # Check if login session is invalidated.
    #     if account.get('login') is None: raise ValueError
    #     if account.get('disabled'):
    #         logging.info("Session authentication: DISABLED %s",
    #                      account['email'])
    #         return None
    #     else:
    #         logging.info("Session authentication: %s", account['email'])
    #         return account

    # def get_current_user_basic(self):
    #     """Get the current user by HTTP Basic authentication.
    #     This should be used only if the site is using TLS (SSL, https).
    #     Raise ValueError if no or erroneous authentication.
    #     """
    #     try:
    #         auth = self.request.headers['Authorization']
    #     except KeyError:
    #         raise ValueError
    #     try:
    #         auth = auth.split()
    #         if auth[0].lower() != 'basic': raise ValueError
    #         auth = base64.b64decode(auth[1])
    #         email, password = auth.split(':', 1)
    #         account = self.get_account(email)
    #         if utils.hashed_password(password) != account.get('password'):
    #             raise ValueError
    #     except (IndexError, ValueError, TypeError):
    #         raise ValueError
    #     if account.get('disabled'):
    #         logging.info("Basic auth login: DISABLED %s", account['email'])
    #         return None
    #     else:
    #         logging.info("Basic auth login: %s", account['email'])
    #         return account
