"Send reminder email to debt-laden members."

from __future__ import print_function

import time

from beerclub import constants
from beerclub import settings
from beerclub import utils


def send_reminders(db, do_print=False):
    "Send reminder email to debt-laden members."
    assert settings['EMAIL']['SENDER']
    assert settings['DEBT_EMAIL_SUBJECT_TEXT']
    assert settings['DEBT_EMAIL_MESSAGE_TEXT']
    view = db.view('event/credit', group_level=1)
    emailserver = utils.EmailServer()
    for row in view:
        if row.value >= settings['DEBT_INSIGNIFICANT']: continue
        member = utils.get_member(db, row.key)
        if member['status'] != constants.ENABLED: continue
        name = u"{} {}".format(member['first_name'], member['last_name'])
        message = settings['DEBT_EMAIL_MESSAGE_TEXT'].format(
            name=name, amount=abs(row.value))
        emailserver.send(member['email'],
                         settings['DEBT_EMAIL_SUBJECT_TEXT'],
                         message)
        if do_print: print(member['email'], row.value)
        time.sleep(settings['EMAIL_PAUSE'])


if __name__ == "__main__":
    utils.setup()
    utils.initialize()
    send_reminders(utils.get_db(), do_print=True)
