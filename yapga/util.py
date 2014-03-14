import bisect
import collections
import contextlib
import itertools
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


def chunks(it, size):
    """Return `size` sized iterable chunks of the iterable `it`.

    This does not detect when `it` is exhausted and will return empty
    iterables forever. It's up to the caller to detect the exhaused
    iterable (i.e. by checking for zero-length results) if they're
    concerned about that.
    """
    it = iter(it)
    while True:
        yield itertools.islice(it, size)


def index_of(seq, value):
    """Find the index of a `value` in a sorted list `seq`.

    Raises:
        ValueError: `value` is not in `sorted_list`.
    """

    idx = bisect.bisect_left(seq, value)
    if idx >= len(seq) or seq[idx] != value:
        raise ValueError(
            '{} not in input sequence.'.format(
                value))
    return idx
