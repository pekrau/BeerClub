"Various supporting functions."

from __future__ import print_function

import datetime
import email.mime.text
import hashlib
import json
import logging
import os
import smtplib
import string
import sys
import time
import unicodedata
import urlparse
import uuid

import couchdb

import beerclub
from beerclub import constants
from beerclub import designs
from beerclub import settings


def setup():
    "Setup: read settings, set logging."
    with open(os.path.join(settings['ROOT_DIR'], 'settings.json')) as infile:
        site = json.load(infile)
        settings.update(site)
    # Set up logging
    if settings.get('LOGGING_DEBUG'):
        kwargs = dict(level=logging.DEBUG)
    else:
        kwargs = dict(level=logging.INFO)
    try:
        kwargs['format'] = settings['LOGGING_FORMAT']
    except KeyError:
        pass
    try:
        filepath = settings['LOGGING_FILEPATH']
        if not filepath: raise KeyError
        kwargs['filename'] = filepath
    except KeyError:
        pass
    try:
        filemode = settings['LOGGING_FILEMODE']
        if not filemode: raise KeyError
        kwargs['filemode'] = filemode
    except KeyError:
        pass
    logging.basicConfig(**kwargs)
    logging.info("BeerClub version %s", beerclub.__version__)
    logging.info("ROOT_DIR: %s", settings['ROOT_DIR'])
    logging.info("logging debug: %s", settings['LOGGING_DEBUG'])
    # Check required settings
    if not settings['COOKIE_SECRET']:
        logging.error('variable COOKIE_SECRET not set')
        sys.exit(1)
    if not settings['PASSWORD_SALT']:
        logging.error('variable PASSWORD_SALT not set')
        sys.exit(1)
    if not settings['EMAIL']['HOST']:
        logging.error("email host EMAIL['HOST'] not defined")
        sys.exit(1)
    # Compute settings
    if not settings.get('PORT'):
        parts = urlparse.urlparse(settings['BASE_URL'])
        settings['PORT'] = parts.port or 80
    settings['MONEY_DECIMAL_STEP'] = 10**(-settings['MONEY_DECIMAL_PLACES'])
    # Convert format specifiers in statements.
    settings['POLICY_STATEMENT'] = settings['POLICY_STATEMENT'].format(**settings)
    settings['PRIVACY_STATEMENT'] = settings['PRIVACY_STATEMENT'].format(**settings)

def get_dbserver():
    "Get the server connection, with credentials if any."
    server = couchdb.Server(settings['DATABASE_SERVER'])
    if settings.get('DATABASE_ACCOUNT') and settings.get('DATABASE_PASSWORD'):
        server.resource.credentials = (settings.get('DATABASE_ACCOUNT'),
                                       settings.get('DATABASE_PASSWORD'))
    return server

def get_db():
    "Return the handle for the CouchDB database."
    server = get_dbserver()
    try:
        return server[settings['DATABASE_NAME']]
    except couchdb.http.ResourceNotFound:
        raise couchdb.http.ResourceNotFound("CouchDB database '%s' does not exist." %
                       settings.get('DATABASE_NAME'))
    except couchdb.http.Unauthorized:
        raise couchdb.http.Unauthorized("CouchDB account '%s' is not authorized to access database '%s'." %
                       (settings.get('DATABASE_ACCOUNT'), settings.get('DATABASE_NAME')))

def initialize(db=None):
    "Load the design documents, or update."
    if db is None:
        db = get_db()
    designs.load_design_documents(db)

def get_doc(db, key, viewname=None):
    """Get the document with the given id, or from the given view.
    Raise KeyError if not found.
    """
    if viewname is None:
        try:
            return db[key]
        except couchdb.ResourceNotFound:
            raise KeyError
    else:
        result = list(db.view(viewname, include_docs=True, reduce=False)[key])
        if len(result) != 1:
            raise KeyError("%i items found", len(result))
        return result[0].doc

def get_docs(db, viewname, key=None, last=None, **kwargs):
    """Get the list of documents using the named view and
    the given key or interval.
    """
    view = db.view(viewname, include_docs=True, reduce=False, **kwargs)
    if key is None:
        iterator = view
    elif last is None:
        iterator = view[key]
    else:
        iterator = view[key:last]
    return [i.doc for i in iterator]

def get_member(db, email):
    """Get the member identified by the email address.
    If Swish is enabled, then also check if 'email' is
    a Swish number, which must match exactly.
    Raise KeyError if no such member.
    """
    email = email.strip().lower()
    try:
        return get_doc(db, email, 'member/email')
    except KeyError:
        if settings['MEMBER_SWISH']:
            try:
                return get_doc(db, email, 'member/swish')
            except KeyError:
                pass
        raise KeyError("no such member %s" % email)

def get_balances(db, members):
    "Get and set the balances for all input members."
    # Prepare lookup of all input members.
    lookup = {}
    for member in members:
        lookup[member['email']] = member
        # Default balance is zero
        member['balance'] = 0.0
    # Simple but effective: get all balances in one go.
    view = db.view('event/credit', group_level=1, reduce=True)
    for row in view:
        try:
            lookup[row.key]['balance'] = row.value
        except KeyError:
            pass

def get_iuid():
    "Return a unique instance identifier."
    return uuid.uuid4().hex

def hashed_password(password):
    "Return the password in hashed form."
    sha256 = hashlib.sha256(settings['PASSWORD_SALT'])
    sha256.update(to_utf8(password))
    return sha256.hexdigest()

def check_password(password):
    """Check that the password is long and complex enough.
    Raise ValueError otherwise."""
    if len(password) < settings['MIN_PASSWORD_LENGTH']:
        raise ValueError("Password must be at least {0} characters.".
                         format(settings['MIN_PASSWORD_LENGTH']))

def timestamp(days=None):
    """Current date and time (UTC) in ISO format, with millisecond precision.
    Add the specified offset in days, if given.
    """
    instant = datetime.datetime.utcnow()
    if days:
        instant += datetime.timedelta(days=days)
    instant = instant.isoformat()
    return instant[:17] + "%06.3f" % float(instant[17:]) + "Z"

def today(days=None):
    """Current date (UTC) in ISO format.
    Add the specified offset in number of days, if given.
    """
    instant = datetime.datetime.utcnow()
    if days:
        instant += datetime.timedelta(days=days)
    result = instant.isoformat()
    return result[:result.index('T')]

def to_ascii(value):
    "Convert any non-ASCII character to its closest ASCII equivalent."
    if not isinstance(value, unicode):
        value = unicode(value, 'utf-8')
    return unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')

def to_utf8(value):
    "Convert value to UTF-8 representation."
    if isinstance(value, basestring):
        if not isinstance(value, unicode):
            value = unicode(value, 'utf-8')
        return value.encode('utf-8')
    else:
        return value

def normalize_swish(value):
    "Return normalized Swish phone number. Get rid of all non-digits."
    return ''.join([c for c in value if c in string.digits])

def timeit(label):
    logging.debug("%f %f %s", time.clock(), time.time(), label)

class EmailServer(object):
    "A connection to an email server for sending emails."

    def __init__(self):
        """Open the connection to the email server.
        Raise ValueError if no email server host has been defined.
        """
        host = settings['EMAIL']['HOST']
        if not host:
            raise ValueError('no email server host defined')
        try:
            port = settings['EMAIL']['PORT']
        except KeyError:
            self.server = smtplib.SMTP(host)
        else:
            self.server = smtplib.SMTP(host, port=port)
        if settings['EMAIL'].get('TLS'):
            self.server.starttls()
        try:
            user = settings['EMAIL']['USER']
            password = settings['EMAIL']['PASSWORD']
        except KeyError:
            pass
        else:
            self.server.login(user, password)

    def __del__(self):
        "Close the connection to the email server."
        try:
            self.server.quit()
        except AttributeError:
            pass

    def send(self, recipient, subject, text):
        "Send an email."
        mail = email.mime.text.MIMEText(text, 'plain', 'utf-8')
        mail['Subject'] = subject
        mail['From'] = settings['EMAIL']['SENDER']
        mail['To'] = recipient
        self.server.sendmail(settings['EMAIL']['SENDER'],
                             [recipient],
                             mail.as_string())
        logging.debug("Sent email to %s", recipient)
