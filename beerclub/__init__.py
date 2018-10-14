""""BeerClub
A web application to keep track of the beer purchases for registered users.
"""

import os

__version__ = '0.1'

settings = dict(VERSION=__version__,
                GITHUB_HREF="https://github.com/pekrau/BeerClub",
                ROOT_DIR=os.path.dirname(__file__),
                LOGGING_DEBUG=True,
                LOGGING_FORMAT='%(levelname)s [%(asctime)s] %(message)s',
                TORNADO_DEBUG=True,
                DATABASE_SERVER='http://localhost:5984/',
                DATABASE_NAME='beerclub',
                DATABASE_ACCOUNT=None,
                DATABASE_PASSWORD=None,
                COOKIE_SECRET=None, # Set to a secret long string of characters.
                PASSWORD_SALT=None, # Set to a secret long string of characters.
                BASE_URL='http://localhost:8887',
                SITE_NAME='Beer Club',
                ACCOUNT_EMAIL_AUTOENABLE=None,
                EMAIL=dict(HOST=None, # Required!
                           PORT=None,
                           TLS=False,
                           USER=None,
                           PASSWORD=None,
                           SENDER=None),
                LOGIN_MAX_AGE_DAYS=31,
)
