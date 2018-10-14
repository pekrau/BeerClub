"Various constants."

# CouchDB
# For view ranges: CouchDB uses the Unicode Collation Algorithm,
# which is not the same as the ASCII collation sequence.
# The endkey is inclusive, by default.
CEILING = 'ZZZZZZZZ'

# Entity documents
DOCTYPE     = 'beerclub_doctype'
ACCOUNT     = 'account'
EVENT       = 'event'
ENTITIES    = (ACCOUNT, EVENT)

# Account status
PENDING  = 'pending'
ENABLED  = 'enabled'
DISABLED = 'disabled'

# Account roles
ADMIN  = 'admin'
MEMBER = 'member'
ROLES  = (ADMIN, MEMBER)

# Misc
USER_COOKIE = 'beerclub_user'
EMAIL_PATTERN = '*@*.*'
