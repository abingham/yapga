import itertools
import json

import baker

from yapga import create_connection, Change, fetch_changes


@baker.command
def fetch(url,
          filename,
          username=None,
          password=None,
          count=None,
          batch_size=500):
    """Fetch up to `count` changes from the gerrit server at `url`,
    grabbing them in batches of `batch_size`. The results are saved as
    a JSON list of `ChangeInfo` objects into `filename`.

    If `username` and `password` are supplied, then they are used for
    digest authentication with the server.
    """
    if count is not None:
        count = int(count)
    if batch_size is not None:
        batch_size = int(batch_size)

    conn = create_connection(url, username, password)
    changes = list(
        itertools.islice(
            fetch_changes(conn, batch_size=batch_size), count))
    with open(filename, 'w') as f:
        f.write(json.dumps(changes))


@baker.command
def list_changes(filename):
    """List all of the change-ids in `filename`.
    """
    with open(filename, 'r') as f:
        changes = json.loads(f.read())
    for c in (Change(d) for d in changes):
        print(c.id)


@baker.command
def rev_size_vs_count(filename, outfile):
    """Log-x scatter of patch size vs. # of commits
    to a review.
    """
    with open(filename, 'r') as f:
        changes = json.loads(f.read())

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
    with open(filename, 'r') as f:
        changes = json.loads(f.read())

    vals = [len(list(Change(c).revisions)) for c in changes]

    import matplotlib.pyplot as plt
    plt.hist(vals, bins=30)
    plt.savefig(outfile)


if __name__ == '__main__':
    baker.run()
