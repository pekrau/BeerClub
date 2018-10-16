""""BeerClub
A web application to keep track of the beer purchases for registered users.
"""

import os

__version__ = '0.3'

settings = dict(
    VERSION=__version__,
    SITE_NAME='Beer Club',
    BASE_URL='http://localhost:8888',
    GITHUB_HREF="https://github.com/pekrau/BeerClub",
    ROOT_DIR=os.path.dirname(__file__),
    LOGGING_DEBUG=True,
    LOGGING_FORMAT='%(levelname)s [%(asctime)s] %(message)s',
    TORNADO_DEBUG=True,
    DATABASE_SERVER='http://localhost:5984/',
    DATABASE_NAME='beerclub',
    DATABASE_ACCOUNT=None,
    DATABASE_PASSWORD=None,
    COOKIE_SECRET=None, # Set to a secret long string of random characters.
    PASSWORD_SALT=None, # Set to a secret long string of random characters.
    MIN_PASSWORD_LENGTH=8,
    ACCOUNT_EMAIL_AUTOENABLE=None,
    EMAIL=dict(HOST='localhost',
               PORT=None,
               TLS=False,
               USER=None,
               PASSWORD=None,
               SENDER=None),
    LOGIN_MAX_AGE_DAYS=31,
    HISTORY_COUNT=40,
    CURRENCY='SEK',
    BEVERAGE=[
        dict(identifier='beer',
             label='beer',
             price=20,
             description='One can or bottle of beer.'),
        dict(identifier='soft',
             label='soft drink',
             price=10,
             description='One can or bottle of soft drink.')
        ],
    PAYMENT=[
        dict(identifier='cash',
             change=False,
             label='cash',
             style='success',
             action='I pay cash.',
             description='I paid cash for one %s.'),
        dict(identifier='swish',
             change=True,
             label='Swish',
             style='info',
             action='I pay to the Swish account.',
             description='I paid for one %s to the Swish account.'),
        dict(identifier='credit',
             change=True,
             label='credit',
             style='warning',
             action='Put it on my credit.',
             description='Put the amount for one %s on my credit.')],
)
