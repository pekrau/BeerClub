"Various supporting functions."

import email.mime.text
import hashlib
import json
import logging
import sys
import urlparse
import uuid

import couchdb

import beerclub
from beerclub import settings


def setup():
    "Setup: read settings, set logging."
    try:
        with open('settings.json') as infile:
            site = json.load(infile)
            settings.update(site)
    except IOError:
        pass
    if not settings['COOKIE_SECRET']:
        logging.error('variable COOKIE_SECRET not set')
        sys.exit(1)
    if not settings['PASSWORD_SALT']:
        logging.error('variable PASSWORD_SALT not set')
        sys.exit(1)
    if not settings['EMAIL']['HOST']:
        logging.error("email host EMAIL['HOST'] not defined")
        sys.exit(1)
    parts = urlparse.urlparse(settings['BASE_URL'])
    settings['PORT'] = parts.port or 80
    if settings.get('LOGGING_DEBUG'):
        kwargs = dict(level=logging.DEBUG)
    else:
        kwargs = dict(level=logging.INFO)
    try:
        kwargs['format'] = settings['LOGGING_FORMAT']
    except KeyError:
        pass
    logging.basicConfig(**kwargs)
    logging.info("BeerClub version %s", beerclub.__version__)
    logging.info("ROOT_DIR: %s", settings['ROOT_DIR'])
    logging.info("logging debug: %s", settings['LOGGING_DEBUG'])

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
        raise KeyError("CouchDB database '%s' does not exist." % 
                       settings['DATABASE_NAME'])

def load_design_documents(db):
    "Load the design documents (view index definitions)."
    views = dict(email=
"""function(doc) {
  if (doc.beerclub_doctype !== 'account') return;
  emit(doc.email, null);
}""")
    update_design_document(db, 'account', views)

def update_design_document(db, design, views=dict()):
    "Update the design document (view index definition)."
    docid = "_design/%s" % design
    try:
        doc = db[docid]
    except couchdb.http.ResourceNotFound:
        logging.info("loading design document %s", docid)
        db.save(dict(_id=docid, views=views))
    else:
        if doc['views'] != views:
            doc['views'] = views
            logging.info("updating design document %s", docid)
            db.save(doc)

def get_doc(db, key, viewname=None):
    """Get the document with the given i, or from the given view.
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

def get_account(db, email):
    """Get the account identified by the email address.
    Raise KeyError if no such account.
    """
    try:
        doc = get_doc(db, email.strip().lower(), 'account/email')
    except KeyError:
        raise KeyError("no such account %s" % email)
    if doc[constants.DOCTYPE] != constants.ACCOUNT:
        raise KeyError("document %s is not an account" % email)
    return doc

def get_iuid():
    "Return a unique instance identifier."
    return uuid.uuid4().hex

def hashed_password(password):
    "Return the password in hashed form."
    sha256 = hashlib.sha256(settings['PASSWORD_SALT'])
    sha256.update(password)
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
    Add the specified offset in days, if given.
    """
    instant = datetime.datetime.utcnow()
    if days:
        instant += datetime.timedelta(days=days)
    result = instant.isoformat()
    return result[:result.index('T')]


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
        self.email = settings.get('SITE_EMAIL') or settings['EMAIL']['SENDER']

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
        mail['From'] = self.email
        mail['To'] = recipient
        self.server.sendmail(self.email, [recipient], mail.as_string())
