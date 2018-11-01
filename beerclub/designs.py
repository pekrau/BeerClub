"CouchDB design documents (view index definitions)."

import logging

import couchdb


DESIGNS = dict(

    member=dict(
        email=dict(map=         # member/email
"""function(doc) {
  if (doc.beerclub_doctype !== 'member') return;
  emit(doc.email, doc.status);
}"""),
        role=dict(map=          # member/role
"""function(doc) {
  if (doc.beerclub_doctype !== 'member') return;
  emit(doc.role, doc.email);
}"""),
        status=dict(map=        # member/status
"""function(doc) {
  if (doc.beerclub_doctype !== 'member') return;
  emit(doc.status, doc.email);
}"""),
        swish=dict(map=         # member/swish
"""function(doc) {
  if (doc.beerclub_doctype !== 'member') return;
  if (!doc.swish) return;
  emit(doc.swish, doc.email);
}"""),
        api_key=dict(map=       # member/api_key
"""function(doc) {
  if (doc.beerclub_doctype !== 'member') return;
  if (!doc.api_key) return;
  emit(doc.api_key, doc.email);
}"""),
    ),

    event=dict(
        credit=dict(reduce="_sum", # event/credit
                    map=
"""function(doc) {
  if (doc.beerclub_doctype !== 'event') return;
  emit(doc.member, doc.credit);
}"""),
        beverage=dict(reduce="_count", # event/beverage
                       map=
"""function(doc) {
  if (doc.beerclub_doctype !== 'event') return;
  if (doc.action !== 'purchase') return;
  emit([doc.member, doc.log.date], doc.beverage);
}"""),
        member=dict(map=       # event/member
"""function(doc) {
  if (doc.beerclub_doctype !== 'event') return;
  emit([doc.member, doc.log.timestamp], null);
}"""),
        ledger=dict(reduce="_sum", # event/ledger
                    map=
"""function(doc) {
  if (doc.beerclub_doctype !== 'event') return;
  emit(doc.log.timestamp, doc.credit);
}"""),
        activity=dict(map=      # event/activity
"""function(doc) {
  if (doc.beerclub_doctype !== 'event') return;
  if (!doc.credit) return;
  emit(doc.log.timestamp, doc.member);
}"""),
        payment=dict(reduce="_sum", # event/payment
                     map=
"""function(doc) {
  if (doc.beerclub_doctype !== 'event') return;
  if (doc.action !== 'payment') return;
  emit(doc.date, doc.credit);
}"""),
    ),
    snapshot=dict(
        date=dict(map=
"""function(doc) {
  if (doc.beerclub_doctype !== 'snapshot') return;
  emit(doc.date, doc.balance);
}""")
    ),
)


def load_design_documents(db):
    "Load the design documents (view index definitions)."
    for entity, designs in DESIGNS.items():
         updated = update_design_document(db, entity, designs)
         if updated:
            for view in designs:
                name = "%s/%s" % (entity, view)
                logging.info("regenerating index for view %s" % name)
                list(db.view(name, limit=10))

def update_design_document(db, design, views):
    "Update the design document (view index definition)."
    docid = "_design/%s" % design
    try:
        doc = db[docid]
    except couchdb.http.ResourceNotFound:
        logging.info("loading design document %s", docid)
        db.save(dict(_id=docid, views=views))
        return True
    else:
        if doc['views'] != views:
            doc['views'] = views
            logging.info("updating design document %s", docid)
            db.save(doc)
            return True
        return False
