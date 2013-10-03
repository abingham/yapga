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
    conn = create_connection(url, username, password)
    changes = list(
        itertools.islice(
            fetch_changes(conn, batch_size=batch_size), count))
    with open(filename, 'w') as f:
        f.write(json.dumps(changes))


@baker.command
def list_changes(url, username=None, password=None):
    conn = create_connection(url,
                             username,
                             password)
    for c in itertools.islice(changes(conn), 100):
        print(c.data)


@baker.command
def rev_size_vs_count(filename, outfile):
    with open(filename, 'r') as f:
        changes = json.loads(f.read())

    data = []
    for c in (Change(d) for d in changes):
        revs = list(c.revisions)
        if revs:
            data.append([len(revs), revs[0].size()])

    data = list(zip(*data))

    import matplotlib.pyplot as plt
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.scatter(data[1], data[0])
    plt.savefig(outfile)

if __name__ == '__main__':
    baker.run()
