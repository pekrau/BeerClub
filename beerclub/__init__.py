""""BeerClub
A web application to keep track of the beer tabs for registered users.
"""

import os

__version__ = '0.1'

settings = dict(ROOT_DIR=os.path.dirname(__file__),
                LOGGING_DEBUG=True,
                LOGGING_FORMAT='%(levelname)s [%(asctime)s] %(message)s',
                TORNADO_DEBUG=True,
                COOKIE_SECRET='secret longish string of characters',
                DATABASE_SERVER='http://localhost:5984/',
                DATABASE_NAME='beerclub',
                DATABASE_ACCOUNT=None,
                DATABASE_PASSWORD=None,
                BASE_URL='http://localhost:8887')
