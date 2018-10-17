"Various constants."

BEERCLUB = 'beerclub'

# CouchDB
# For view ranges: CouchDB uses the Unicode Collation Algorithm,
# which is not the same as the ASCII collation sequence.
# The endkey is inclusive, by default.
CEILING = 'ZZZZZZZZ'

# Entity documents
DOCTYPE  = 'beerclub_doctype'
ACCOUNT  = 'account'
EVENT    = 'event'
ENTITIES = (ACCOUNT, EVENT)
META     = 'meta'

# Account status
PENDING  = 'pending'
ENABLED  = 'enabled'
DISABLED = 'disabled'

# Account roles
ADMIN  = 'admin'
MEMBER = 'member'
ROLES  = (ADMIN, MEMBER)

# Event actions
PURCHASE    = 'purchase'
REPAYMENT   = 'repayment'
EXPENDITURE = 'expenditure'

# Boolean string values
TRUE  = frozenset(['true', 'yes', 't', 'y', '1'])
FALSE = frozenset(['false', 'no', 'f', 'n', '0'])

# Misc
USER_COOKIE = 'beerclub_user'
EMAIL_PATTERN = '*@*.*'
