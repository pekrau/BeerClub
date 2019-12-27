"Various constants."

BEERCLUB = 'beerclub'

# CouchDB
# For view ranges: CouchDB uses the Unicode Collation Algorithm,
# which is not the same as the ASCII collation sequence.
# The endkey is inclusive, by default.
CEILING = 'ZZZZZZZZ'

# Entity documents
DOCTYPE  = 'beerclub_doctype'
MEMBER   = 'member'
EVENT    = 'event'
SNAPSHOT = 'snapshot'
ENTITIES = (MEMBER, EVENT, SNAPSHOT)

# Member status
PENDING  = 'pending'
ENABLED  = 'enabled'
DISABLED = 'disabled'
STATUSES = (PENDING, ENABLED, DISABLED)

# Member roles
ADMIN  = 'admin'
MEMBER = 'member'
ROLES  = (ADMIN, MEMBER)

# Event actions
TRANSFER = 'transfer'           # Bank account transfer into Beer Club account.
PURCHASE = 'purchase'           # Purchase of beer for the Beer Club.
PAYMENT  = 'payment'            # Paying for beer from the Beer Club.
CASH     = 'cash'               # Cash transfer into Beer Club acount.

# Payment identifier (hardwired)
EXPENDITURE = 'expenditure'

# Misc
CORRECTION = '__correction__'
USER_COOKIE = 'beerclub_user'
EMAIL_PATTERN = '*@*.*'
API_KEY_HEADER = 'X-BeerClub-API-key'
JSON_MIME = 'application/json'
CSV_MIME  = 'text/csv'
