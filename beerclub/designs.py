"CouchDB design documents (view index definitions)."

import logging

import couchdb


ACCOUNT_EMAIL = dict(map=
"""function(doc) {
  if (doc.beerclub_doctype !== 'account') return;
  emit(doc.email, doc.status);
}""")

ACCOUNT_ROLE = dict(map=
"""function(doc) {
  if (doc.beerclub_doctype !== 'account') return;
  emit(doc.role, doc.email);
}""")

ACCOUNT_STATUS = dict(map=
"""function(doc) {
  if (doc.beerclub_doctype !== 'account') return;
  emit(doc.status, doc.email);
}""")

EVENT_ACTION = dict(map=
"""function(doc) {
  if (doc.beerclub_doctype !== 'event') return;
  emit(doc.action, doc.account);
}""")

EVENT_CREDIT = dict(reduce="_sum",
                    map=
"""function(doc) {
  if (doc.beerclub_doctype !== 'event') return;
  emit(doc.account, doc.credit);
}""")

EVENT_BEVERAGES = dict(reduce="_count",
                       map=
"""function(doc) {
  if (doc.beerclub_doctype !== 'event') return;
  if (doc.action !== 'purchase') return;
  emit([doc.account, doc.log.date], doc.beverage);
}""")

EVENT_ACCOUNT = dict(map=
"""function(doc) {
  if (doc.beerclub_doctype !== 'event') return;
  emit([doc.account, doc.log.timestamp], null);
}""")

EVENT_TIMESTAMP = dict(map=
"""function(doc) {
  if (doc.beerclub_doctype !== 'event') return;
  emit(doc.log.timestamp, doc.account);
}""")


def load_design_documents(db):
    "Load the design documents (view index definitions)."
    update_design_document(db, 'account', dict(email=ACCOUNT_EMAIL,
                                               role=ACCOUNT_ROLE,
                                               status=ACCOUNT_STATUS))
    update_design_document(db, 'event', dict(action=EVENT_ACTION,
                                             credit=EVENT_CREDIT,
                                             beverages=EVENT_BEVERAGES,
                                             account=EVENT_ACCOUNT,
                                             timestamp=EVENT_TIMESTAMP))

def update_design_document(db, design, views):
    "Update the design document (view index definition)."
    docid = "_design/%s" % design
    try:
        doc = db[docid]
    except couchdb.http.ResourceNotFound:
        logging.info("loading design document %s", docid)
        db.save(dict(_id=docid, views=views))
    else:
        if doc['views'] != views:
            doc['views'] = views
            logging.info("updating design document %s", docid)
            db.save(doc)
