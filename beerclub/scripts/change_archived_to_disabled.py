"Change all archived members to disabled. In order to remove status 'archived'."

from __future__ import print_function

from beerclub import constants
from beerclub import utils


def change_to_disabled(db):
    for member in utils.get_docs(db, 'member/status', key=constants.ARCHIVED):
        print(member['email'])
        member['status'] = constants.DISABLED
        db.save(member)


if __name__ == "__main__":
    import sys
    utils.setup()
    utils.initialize()
    change_to_disabled(utils.get_db())
