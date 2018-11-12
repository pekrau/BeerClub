"Correct anspshots retroactively."

from __future__ import print_function

from beerclub import constants
from beerclub import utils


def correct_snapshots(db):
    transfer = 0.0
    credits = {}
    payments = {}
    snapshots = dict([(s['date'], s)
                      for s in utils.get_docs(db, 'snapshot/date')])
    for date in snapshots:
        credits[date] = 0.0
        payments[date] = 0.0
    for event in utils.get_docs(db, 'event/credit'):
        if event['action'] == constants.TRANSFER:
            transfer += event['credit']
        key = event['log']['timestamp'][:10]
        try:
            credits[key] += event['credit']
        except KeyError:
            credits[key] = event['credit']
    print('transfer', transfer)
    for event in utils.get_docs(db, 'event/payment'):
        if event['action'] == constants.PAYMENT:
            try:
                payments[event['date']] += event['credit']
            except KeyError:
                payments[event['date']] = event['credit']
    print('credits')
    accum = 0.0
    for key, credit in sorted(credits.items()):
        credits[key] += accum
        accum += credit
        print(key, credit, credits[key])
    print()
    print('payments')
    accum = 0.0
    for date, credit in sorted(payments.items()):
        payments[date] += accum
        accum += credit
        print(date, credit, payments[date])

    snapshots = dict([(s['date'], s)
                      for s in utils.get_docs(db, 'snapshot/date')])
    for date, snapshot in sorted(snapshots.items()):
        snapshot.pop('balance', None)
        try:
            snapshot['beerclub_balance'] = payments[date]
            snapshot['members_balance'] = credits[date]
        except KeyError:
            print('no payment/credit for', date)
            # db.delete(snapshot)
        else:
            db.save(snapshot)


if __name__ == "__main__":
    utils.setup()
    utils.initialize()
    correct_snapshots(utils.get_db())
