"Send reminder email to debt-laden members."

from __future__ import print_function

import time

import couchdb

from beerclub import settings
from beerclub import utils


INSIGNIFICANT_DEBT = -20
BIG_DEBT           = -500

PAUSE = 3.0

SUBJECT_TEXT = "Your debt to the SciLifeLab Beer Club"

SUBJECT_BIG_DEBT_TEXT = "Time to pay your SciLifeLab Beer Club debt"

MESSAGE_TEXT = """Hello {},
According to my notes, you owe the SciLifeLab Beer Club {} SEK."""

BIG_DEBT_MESSAGE_TEXT = "This is a rather large sum, and it is time that you pay up."

PAYMENT_TEXT = """Please pay the amount you owe to the Beer Club by:

Alt 1) Swish 070-639 96 35 (Per Kraulis).

Alt 2) SEB bank account 5694 06 421 88. Include your name in the message field!
       This is an account dedicated to handling only Beer Club money.

The SciLifeLab Beer Club site at https://beerclub.scilifelab.se/
has all information, including the current balance of your member account.

If you have paid yesterday or today, your account may not have been updated.
If so, ignore this message.

/Per Kraulis
SciLifeLab Beer Club administrator
"""


def send_reminders(db):
    "Send reminder email to debt-laden members."
    view = db.view(


if __name__ == "__main__":
    utils.setup()
    utils.initialize()
    send_reminders(utils.get_db())
