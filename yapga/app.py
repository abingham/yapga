import itertools
import json
import logging

import baker

from yapga import create_connection, Change, fetch_changes
import yapga.util

log = logging.getLogger('yapga')


@baker.command
def fetch(url,
          filename,
          username=None,
          password=None,
          count=None,
          batch_size=500,
          start_at=None,
          status='merged'):
    """Fetch up to `count` changes from the gerrit server at `url`,
    grabbing them in batches of `batch_size`. The results are saved as
    a JSON list of `ChangeInfo` objects into `filename`.

    If `username` and `password` are supplied, then they are used for
    digest authentication with the server.
    """
    queries = ['q=status:{}'.format(status),
               'o=ALL_REVISIONS',
               'o=ALL_FILES',
               'o=ALL_COMMITS',
               'n={}'.format(batch_size)]

    if start_at is not None:
        queries.append('N={}'.format(start_at))

    if count is not None:
        count = int(count)

    conn = create_connection(url, username, password)
    chunks = yapga.util.chunks(
        itertools.islice(fetch_changes(conn, queries=queries),
                         count),
        batch_size)

    changes = []
    try:
        for chunk in (list(c) for c in chunks):
            if not chunk:
                break
            changes.extend(chunk)
    except Exception:
        log.exception('Error fetching results. Partial results will be saved to {}'.format(filename))
    finally:
        log.info('{} changes retrieved.'.format(len(changes)))
        if changes:
            with open(filename, 'w') as f:
                f.write(json.dumps(changes))


@baker.command
def list_changes(filename):
    """List all of the change-ids in `filename`.
    """
    changes = yapga.util.load_changes(filename)
    for c in (Change(d) for d in changes):
        print(c.id)


@baker.command
def rev_size_vs_count(filename, outfile):
    """Log-x scatter of patch size vs. # of commits
    to a review.
    """
    changes = yapga.util.load_changes(filename)

    data = []
    for c in (Change(d) for d in changes):
        revs = list(c.revisions)
        if revs:
            data.append([len(revs), revs[0].size()])

    data = list(zip(*data))

    import numpy
    print('corr. coeff:', numpy.corrcoef(data))

    import matplotlib.pyplot as plt
    plt.scatter(data[1], data[0], marker=',')
    plt.xscale('log')
    plt.xlim(1, max(data[1]))
    #plt.savefig(outfile)
    plt.show()


@baker.command
def rev_count_hist(filename, outfile):
    changes = yapga.util.load_changes(filename)

    log.info('Scanning {} changes'.format(len(changes)))

    vals = [len(list(Change(c).revisions)) for c in changes]

    import matplotlib.pyplot as plt
    plt.hist(vals, bins=30)
    plt.savefig(outfile)


@baker.command
def changes_by_owner(filename):
    changes = yapga.util.load_changes(filename)

    counts = {}

    for change in (Change(c) for c in changes):
        o = change.owner.name
        counts[o] = counts.get(o, 0) + 1

    counts = sorted(counts.items(), key=lambda x: x[1])
    for c in counts:
        print((c[1] // 10) * '*', c[0])


if __name__ == '__main__':
    baker.run()
