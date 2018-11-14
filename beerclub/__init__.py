""""BeerClub
A web application to keep track of the beer purchases for registered users.
"""

import os

__version__ = '1.5.9'

settings = dict(
    VERSION=__version__,
    ROOT_DIR=os.path.dirname(__file__),
    SITE_NAME='Beer Club',
    BASE_URL='http://localhost:8888',
    GITHUB_HREF="https://github.com/pekrau/BeerClub",
    LOGGING_DEBUG=False,
    TORNADO_DEBUG=False,
    LOGGING_FORMAT='%(levelname)s [%(asctime)s] %(message)s',
    LOGGING_FILEPATH=None,
    LOGGING_FILEMODE=None,
    LOCALE_MONETARY=None,
    DATABASE_SERVER='http://localhost:5984/',
    DATABASE_NAME='beerclub',
    DATABASE_ACCOUNT=None,
    DATABASE_PASSWORD=None,
    COOKIE_SECRET=None, # Set to a secret long string of random characters.
    PASSWORD_SALT=None, # Set to a secret long string of random characters.
    MIN_PASSWORD_LENGTH=8,
    LOGIN_SESSION_DAYS=31,
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
    DISPLAY_ACCOUNT_DAYS=7,
    DISPLAY_PAYMENT_DAYS=7,
    DISPLAY_SNAPSHOT_DAYS=31,
    CONTACT_EMAIL=None,
    GLOBAL_ALERT=None,
    RULES_HTML="<ul><li>You must be a registered member to buy beer.</li></ul>",
    PAYMENT_INFO_HTML=None,
    POLICY_STATEMENT="The {SITE_NAME} is a non-profit group arranging pub"
    " evenings for its members. Volunteer members must obtain the beer"
    " from the shop, and will be reimbursed by the {SITE_NAME} administrator.",
    PRIVACY_STATEMENT="By registering, you agree to allow the personal data"
    " you provide to be handled by the {SITE_NAME} according to"
    " applicable laws. No data will be transferred to any external entity.",
    MEMBER_SWISH=True,   # Enable Swish phone number field for member.
    MEMBER_ADDRESS=True, # Enable address field for member.
    CREDIT_CLASSES=[(-500, 'bg-danger text-light'),
                    (-250, 'bg-warning'),
                    (-1, 'text-danger')],
    BEVERAGE=[
        dict(identifier='beer',
             label='beer',
             price=20,
             description='One can or bottle of beer.'),
    ],
    PURCHASE=[
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
    PAYMENT=[
        dict(identifier='cash',
             label='Cash paid to the admin.',
             default=True),
        dict(identifier='swish',
             label='Verified Swish payment.'),
        dict(identifier='bank',
             label='Bank account transfer.'),
    ],
    CURRENCY='kr',
    MONEY_DECIMAL_PLACES=2,
    MONEY_DECIMAL_POINT='.',
    MONEY_THOUSAND_DELIMITER=',',
)
