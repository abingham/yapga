import itertools
import json
import logging

import baker

import matplotlib
matplotlib.use('TkAgg')

import numpy as np

import yapga
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

    conn = yapga.create_connection(url, username, password)
    chunks = yapga.util.chunks(
        itertools.islice(yapga.fetch_changes(conn, queries=queries),
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
def fetch_reviewers(change_file,
                    url,
                    filename,
                    username=None,
                    password=None):
    """Fetch all reviewers for the changes in `change_file` from `url`. The
    results are written to `filename` as a json map from change-id to
    review-list.
    """

    conn = yapga.create_connection(url, username, password)

    data = {}
    for c in yapga.util.load_changes(change_file):
        try:
            data[c.id] = yapga.fetch_reviewers(conn, c.id)
        except Exception:
            log.exception('Error fetching reviewers for change {}'.format(c.id))

    with open(filename, 'w') as f:
        f.write(json.dumps(data))


@baker.command
def list_changes(filename):
    """List all of the change-ids in `filename`.
    """
    for c in yapga.util.load_changes(filename):
        print(c.id)


@baker.command
def rev_size_vs_count(filename, outfile=None):
    """Log-x scatter of patch size vs. # of commits
    to a review.
    """
    data = []

    for c in yapga.util.load_changes(filename):
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

    if outfile:
        plt.savefig(outfile)

    plt.show()


@baker.command
def rev_count_hist(filename, outfile=None):
    changes = list(yapga.util.load_changes(filename))

    log.info('Scanning {} changes'.format(len(changes)))

    vals = [len(list(c.revisions)) for c in changes]

    import matplotlib.pyplot as plt
    plt.hist(vals, bins=30)

    if outfile:
        plt.savefig(outfile)

    plt.show()


@baker.command
def changes_by_owner(filename):
    counts = {}

    for change in yapga.util.load_changes(filename):
        o = change.owner.name
        counts[o] = counts.get(o, 0) + 1

    counts = sorted(counts.items(), key=lambda x: x[1])
    for c in counts:
        print((c[1] // 10) * '*', c[0])


@baker.command
def list_messages(filename):
    for change in yapga.util.load_changes(filename):
        print(list(change.messages))


@baker.command
def list_reviewers(filename):
    for change in yapga.util.load_changes(filename):
        for r in change.reviewers:
            print(r.name)


@baker.command
def compare_reviewers(changes, reviews):
    """Heatmap showing how often reviewers review change owners.

    Not very useful right now. Need to weed out the useless,
    one-offers and stuff.
    """
    # http://stackoverflow.com/questions/14391959/heatmap-in-matplotlib-with-pcolor
    reviews = dict(yapga.util.load_reviews(reviews))
    changes = list(yapga.util.load_changes(changes))

    owner_map = dict(
        zip(set(c.owner.email for c in changes),
            itertools.count()))

    reviewer_map = dict(
        zip(set(r.email for revs in reviews.values() for r in revs),
            itertools.count()))

    data = np.zeros((len(reviewer_map), len(owner_map)))

    for change in changes:
        owner_idx = owner_map[change.owner.email]
        for reviewer in reviews.get(change.id, []):
            reviewer_idx = reviewer_map[reviewer.email]
            data[(reviewer_idx, owner_idx)] += 1

    import matplotlib.pyplot as plt
    fig, ax = plt.subplots()

    print('calculating heatmap...')
    heatmap = ax.pcolor(data)
    print('heatmap calculated')

    # ordered_emails = [x[0] for x in sorted(id_map.items(), key=lambda i: i[1])]

    #ax.set_xticklabels(ordered_emails)
    #ax.set_yticklabels(ordered_emails)

    plt.show()

        # try:
        #     review = reviews[change.id]
        #     print(review)
        # except KeyError:
        #     pass


if __name__ == '__main__':
    baker.run()
