import bisect
import itertools


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


def is_empty(i):
    try:
        next(iter(i))
        return False
    except StopIteration:
        return True