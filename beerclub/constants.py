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
ENTITIES = (MEMBER, EVENT)

# Member status
PENDING  = 'pending'
ENABLED  = 'enabled'
DISABLED = 'disabled'

# Member roles
ADMIN  = 'admin'
MEMBER = 'member'
ROLES  = (ADMIN, MEMBER)

# Event actions
PURCHASE    = 'purchase'
REPAYMENT   = 'repayment'
EXPENDITURE = 'expenditure'

# Misc
USER_COOKIE = 'beerclub_user'
EMAIL_PATTERN = '*@*.*'
