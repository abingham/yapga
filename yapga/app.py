import itertools

import baker

from yapga import changes, create_connection


@baker.command
def list_changes(url, username=None, password=None):
    conn = create_connection(url,
                             username,
                             password)
    for c in itertools.islice(changes(conn), 100):
        print(c.data)


@baker.command(default=True)
def list_all_revisions(url, username=None, password=None):
    conn = create_connection(url,
                             username,
                             password)

    data = []
    for c in itertools.islice(changes(conn, batch_size=500), 10000):
        revs = list(c.revisions)
        if revs:
            data.append([len(revs), revs[0].size()])

    data = list(zip(*data))

    import matplotlib.pyplot as plt
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.scatter(data[1], data[0])
    ax.set_xscale('log')
    plt.savefig('android.png')

if __name__ == '__main__':
    baker.run()
