"""Dump the database into a tar.gz file.

By default, the dump file will be called 'dump_{ISO date}.tar.gz'
using today's date.
"""

import argparse
import cStringIO
import json
import logging
import os
import sys
import tarfile
import time

from beerclub import constants
from beerclub import utils


def dump(db, filepath):
    """Dump contents of the database to a tar file, optionally gzip compressed.
    Skip any entity that does not contain a doctype field.
    """
    count_items = 0
    count_files = 0
    if filepath.endswith('.gz'):
        mode = 'w:gz'
    else:
        mode = 'w'
    outfile = tarfile.open(filepath, mode=mode)
    for key in db:
        doc = db[key]
        # Only documents that explicitly belong to the application.
        if doc.get(constants.DOCTYPE) is None: continue
        del doc['_rev']
        info = tarfile.TarInfo(doc['_id'])
        data = json.dumps(doc)
        info.size = len(data)
        outfile.addfile(info, cStringIO.StringIO(data))
        count_items += 1
        for attname in doc.get('_attachments', dict()):
            info = tarfile.TarInfo("{0}_att/{1}".format(doc['_id'], attname))
            attfile = db.get_attachment(doc, attname)
            if attfile is None:
                data = ''
            else:
                data = attfile.read()
                attfile.close()
            info.size = len(data)
            outfile.addfile(info, cStringIO.StringIO(data))
            count_files += 1
    outfile.close()
    logging.info("dumped %s items and %s files to %s",
                 count_items, count_files, filepath)


if __name__ == '__main__':
    utils.setup()
    utils.initialize()
    parser = argparse.ArgumentParser(description='Write dump of database.')
    parser.add_argument('-d', '--dumpfile', metavar='FILE',
                        action='store', dest='dumpfile',
                        help='The full path of the dump file.')
    parser.add_argument('-D', '--dumpdir', metavar='DIR',
                        action='store', dest='dumpdir',
                        help='The directory to write the dump file'
                        ' (with standard name) in.')
    args = parser.parse_args()
    if args.dumpfile:
        filepath = args.dumpfile
    else:
        filepath = "dump_{0}.tar.gz".format(time.strftime("%Y-%m-%d"))
        if args.dumpdir:
            filepath = os.path.join(args.dumpdir, filepath)
    dump(utils.get_db(), filepath)
