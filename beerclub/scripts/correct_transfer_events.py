"Correct transfer events from action 'payment' to 'transfer'."

from __future__ import print_function

from beerclub import constants
from beerclub import utils


def correct_transfer_events(db):
    for event in utils.get_docs(db, 'event/payment'):
        if event['description'] != 'transfer': continue
        event['action'] = constants.TRANSFER
        event['description'] = 'from previous system'
        print(event['member'], event['credit'])
        db.save(event)


if __name__ == "__main__":
    import sys
    utils.setup()
    utils.initialize()
    correct_transfer_events(utils.get_db())
