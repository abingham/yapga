import itertools
import json

from yapga.gerrit_api import Change


def load_changes(filename):
    with open(filename, 'r') as f:
        changes = json.loads(f.read())

    for c in changes:
        yield Change(c)

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
