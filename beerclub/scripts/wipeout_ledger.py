"Remove all events and snapshots from the database, but keep the members."

from beerclub import constants
from beerclub import utils


def wipeout_ledger(db):
    "Remove all events and snapshots from the database, but keep the members."
    for name in db:
        doc = db[name]
        try:
            if doc[constants.DOCTYPE] == constants.MEMBER: continue
        except KeyError:
            pass
        else:
            db.delete(doc)


if __name__ == "__main__":
    utils.setup()
    utils.initialize()
    wipeout_ledger(utils.get_db())
