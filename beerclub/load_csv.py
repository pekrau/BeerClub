"Load a CSV file created from Google Docs. Contains members and their balance."

from __future__ import print_function

import csv
import unicodedata

from beerclub import constants
from beerclub import settings
from beerclub import utils
from beerclub.member import MemberSaver
from beerclub.event import EventSaver


LAST_NAME_COLUMN = 0
FIRST_NAME_COLUMN = 1
ADDRESS_COLUMN = 3
DEBT_COLUMN = 4
ALT_EMAIL_COLUMN = 5
ORD_MINUS_SIGN = 8722

def load_csv(db, filepath):
    "Load the given CSV file."
    with open(filepath, 'rb') as infile:
        reader = csv.reader(infile)
        reader.next()           # Skip header rows
        reader.next()
        for record in reader:
            first_name = record[FIRST_NAME_COLUMN].decode('utf-8')
            last_name = record[LAST_NAME_COLUMN].decode('utf-8')
            try:
                email = record[ALT_EMAIL_COLUMN].strip()
                if not email: raise IndexError
            except IndexError:
                email = "{}.{}@scilifelab.se".format(
                    utils.to_ascii(first_name).lower(),
                    utils.to_ascii(last_name).lower())
            try:
                member = utils.get_member(db, email)
            except KeyError:
                with MemberSaver(db=db) as saver:
                    saver['email']      = email
                    saver['role']       = constants.MEMBER
                    saver['first_name'] = first_name
                    saver['last_name']  = last_name
                    saver['swish']      = None
                    saver['address']   = record[ADDRESS_COLUMN].strip() or None
                member = saver.doc
                print('created', member['email'])
            else:
                print('found', member['email'])
            with EventSaver(db=db) as saver:
                saver['member']  = member['email']
                saver['action']  = constants.REPAYMENT
                saver['payment'] = 'transfer'
                value = record[DEBT_COLUMN].decode('utf-8')
                # Google, what are you doing?
                if ord(value[0]) == ORD_MINUS_SIGN:
                    value = - float(value[1:])
                else:
                    value = float(value)
                saver['credit'] = value
                saver['date']   = utils.today()
            print(value)


if __name__ == "__main__":
    import sys
    utils.setup()
    utils.initialize()
    load_csv(utils.get_db(), sys.argv[1])
