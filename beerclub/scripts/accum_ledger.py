"""Accumulate members, their purchases and payments.
To detect who should be assigned swish_lazy mode.
"""

from __future__ import print_function

ACTION = 0
MEMBER = 2
DESCRIPTION = 4
CREDIT = 5

import csv

with open('ledger.csv', 'rb') as infile:
    reader = csv.reader(infile)
    reader.next()               # Skip header
    rows = list(reader)

print(len(rows))

purchases = dict()
payments = dict()

for row in rows:
    if row[ACTION] == 'payment':
        try:
            payments[row[MEMBER]] += float(row[CREDIT])
        except KeyError:
            payments[row[MEMBER]] = float(row[CREDIT])
    elif row[ACTION] == 'purchase' and row[DESCRIPTION] == 'credit':
        try:
            purchases[row[MEMBER]] += float(row[CREDIT])
        except KeyError:
            purchases[row[MEMBER]] = float(row[CREDIT])

members = set(payments.keys() + purchases.keys())
for member in sorted(members):
    print("%40s %6s %6s" % (member, purchases.get(member, '-'), payments.get(member, '-')))
