import collections
import contextlib

import pymongo

from yapga.gerrit_api import Change, Reviewer

DEFAULT_MONGO_HOST = 'localhost'
DEFAULT_MONGO_PORT = 27017


def escape_struct(s):
    if not isinstance(s, collections.abc.Mapping):
        return s

    for k, v in list(s.items()):
        del s[k]
        s[k.replace('.', '<DOT>').replace('$', '<DOLLAR_SIGN>')] = escape_struct(v)

    return s


@contextlib.contextmanager
def get_db(dbname,
           mongo_host=DEFAULT_MONGO_HOST,
           mongo_port=DEFAULT_MONGO_PORT):
    client = pymongo.MongoClient(mongo_host,
                                 int(mongo_port))
    yield client[dbname]


def insert_change(db, change):
    change_coll = db['changes']
    change_coll.update({'change_id': change['change_id']},
                       escape_struct(change),
                       upsert=True)


def insert_reviewers(db, change_id, reviewers, upsert=True):
    rev_coll = db['reviews']
    rev_coll.update({'change_id': change_id},
                    {'change_id': change_id,
                     'reviewers': escape_struct(reviewers)},
                    upsert=upsert)


def all_changes(db):
    """Read changes from `dbname` and generate a sequence of `Change`
    objects.
    """
    changes = db['changes']

    for c in changes.find():
        yield Change(c)


def all_reviewers(db):
    """Read reviews from `dbname` and generates a sequence of
    `(change-id, [Reviewer, . . .])` tuples.
    """

    reviews = db['reviews']

    for rev in reviews.find():
        yield (rev['change_id'], [Reviewer(r) for r in rev['reviewers']])

def get_reviewers(db, change_id):
    rev_coll = db['reviews']
    for r in rev_coll.find({'change_id': change_id}):
        yield r
