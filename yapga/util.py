import bz2
import contextlib
import gzip
import itertools
import json
import os
import zipfile

from yapga.gerrit_api import Change, Reviewer


extension_map = {
    '.gz': gzip.open,
    '.zip': zipfile.ZipFile,
    '.bz2': bz2.open,
}


@contextlib.contextmanager
def open_file(filename, mode):
    opener = extension_map.get(os.path.splitext(filename)[1], open)
    with opener(filename, mode=mode) as f:
        yield f

def load_changes(filename):
    """Read changes from `filename` and generate a sequence of `Change`
    objects.
    """
    with open_file(filename, 'r') as f:
        changes = json.loads(f.read())

    for c in changes:
        yield Change(c)


def load_reviews(filename):
    """Read reviews from `filename` and generates a sequence of
    `(commit-id, [Reviewer, . . .])` tuples.
    """
    with open_file(filename, 'r') as f:
        data = json.loads(f.read())
    for cid, revs in data.items():
        yield (cid, [Reviewer(r) for r in revs])


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
