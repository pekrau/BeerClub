""""BeerClub
A web application to keep track of the beer purchases for registered users.
"""

import os

__version__ = '0.7'

settings = dict(
    VERSION=__version__,
    SITE_NAME='Beer Club',
    BASE_URL='http://localhost:8888',
    GITHUB_HREF="https://github.com/pekrau/BeerClub",
    ROOT_DIR=os.path.dirname(__file__),
    LOGGING_DEBUG=False,
    LOGGING_FORMAT='%(levelname)s [%(asctime)s] %(message)s',
    TORNADO_DEBUG=False,
    DATABASE_SERVER='http://localhost:5984/',
    DATABASE_NAME='beerclub',
    DATABASE_ACCOUNT=None,
    DATABASE_PASSWORD=None,
    COOKIE_SECRET=None, # Set to a secret long string of random characters.
    PASSWORD_SALT=None, # Set to a secret long string of random characters.
    MIN_PASSWORD_LENGTH=8,
    LOGIN_MAX_AGE_DAYS=31,
    MEMBER_EMAIL_AUTOENABLE=None,
    EMAIL=dict(HOST='localhost',
               PORT=None,
               TLS=False,
               USER=None,
               PASSWORD=None,
               SENDER=None),
    DISPLAY_NAVBAR_THEME='navbar-dark',
    DISPLAY_NAVBAR_BG_COLOR='bg-dark',
    DISPLAY_NAVBAR_STYLE_COLOR=None,
    DISPLAY_ACTIVITY_DAYS=6,
    DISPLAY_LEDGER_DAYS=7,
    CONTACT_EMAIL=None,
    RULES_HTML="<ul><li>You must be a registered member to buy beer.</li></ul>",
    PAYMENT_INFO_HTML=None,
    POLICY_STATEMENT="The {SITE_NAME} is a non-profit group providing beer"
    " to its members. Volunteer members must purchase the beer and deliver"
    " it to the {SITE_NAME}. They will be reimbursed by the {SITE_NAME}"
    " administrator.",
    PRIVACY_STATEMENT="By registering, you agree to allow the personal data"
    " you provide to be handled by the {SITE_NAME} according to"
    " applicable laws. No data will be transferred to any external entity.",
    MONEY_STEP='0.01',
    MEMBER_SWISH=True,   # Enable Swish phone number field for member.
    MEMBER_ADDRESS=True, # Enable address field for member.
    CREDIT_STYLES=[(-1000, 'bg-danger text-light'),
                   (-500, 'bg-warning'),
                   (-1, 'text-danger')],
    BEVERAGE=[
        dict(identifier='beer',
             label='beer',
             price=20,
             description='One can or bottle of beer.'),
    ],
    PAYMENT=[
        dict(identifier='cash',
             change=False,
             label='cash',
             style='success',
             action='I paid cash.',
             description='I paid cash for one %s.'),
        dict(identifier='credit',
             change=True,
             label='credit',
             style='warning',
             action='Put it on my credit.',
             description='Put the amount for one %s on my credit.'),
    ],
    REPAYMENT=[
        dict(identifier='cash',
             label='Cash paid to the admin',
             default=True),
        dict(identifier='bank',
             label='Bank account transferral'),
        dict(identifier='correction',
             label='Correction of an erroneous transaction'),
        dict(identifier='transfer',
             label='Transfer of credit from some other source'),
    ],
)
