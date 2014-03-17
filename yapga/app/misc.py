import collections
import itertools
import logging

import baker
import numpy as np

import yapga.db


log = logging.getLogger('yapga')


@baker.command
def list_changes(dbname,
                 mongo_host=yapga.db.DEFAULT_MONGO_HOST,
                 mongo_port=yapga.db.DEFAULT_MONGO_PORT):
    """List all of the changes in the database `dbname`.
    """
    with yapga.db.get_db(dbname,
                           mongo_host,
                           mongo_port) as db:
        for c in yapga.db.all_changes(db):
            print(c.data)


@baker.command
def rev_size_vs_count(dbname,
                      mongo_host=yapga.db.DEFAULT_MONGO_HOST,
                      mongo_port=yapga.db.DEFAULT_MONGO_PORT,
                      outfile=None):
    """Log-x scatter of patch size vs. # of commits
    to a review.
    """
    data = []

    with yapga.db.get_db(dbname, mongo_host, mongo_port) as db:
        for c in yapga.db.all_changes(db):
            revs = list(c.revisions)
            if revs:
                data.append([len(revs), revs[0].size()])

    data = list(zip(*data))

    import numpy
    print('corr. coeff:', numpy.corrcoef(data))

    import matplotlib.pyplot as plt
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.set_title('Revision size vs. commit count\ndataset: {}'.format(dbname))
    ax.scatter(data[1], data[0], marker=',')

    ax.set_xlim([1, max(data[1])])
    ax.set_xlabel('Size of change')
    ax.set_ylim([0, max(data[0])])
    ax.set_ylabel('Number of patchsets')
    plt.xscale('log')


    if outfile:
        plt.savefig(outfile)

    plt.show()


@baker.command
def rev_count_hist(dbname,
                   mongo_host=yapga.db.DEFAULT_MONGO_HOST,
                   mongo_port=yapga.db.DEFAULT_MONGO_PORT,
                   outfile=None):
    "Histogram of number of revision per change."

    with yapga.db.get_db(dbname, mongo_host, mongo_port) as db:
        changes = list(yapga.db.all_changes(db))

    log.info('Scanning {} changes'.format(len(changes)))

    vals = [len(list(c.revisions)) for c in changes]

    import matplotlib.pyplot as plt
    plt.hist(vals, bins=30)

    if outfile:
        plt.savefig(outfile)

    plt.show()


@baker.command
def changes_by_owner(dbname,
                     mongo_host=yapga.db.DEFAULT_MONGO_HOST,
                     mongo_port=yapga.db.DEFAULT_MONGO_PORT):
    "Simple histogram of change count by owners."
    counts = {}

    with yapga.db.get_db(dbname, mongo_host, mongo_port) as db:
        for change in yapga.db.all_changes(db):
            o = change.owner.name
            counts[o] = counts.get(o, 0) + 1

    counts = sorted(counts.items(), key=lambda x: x[1])
    for c in counts:
        print((c[1] // 10) * '*', c[0])


@baker.command
def list_messages(dbname,
                  mongo_host=yapga.db.DEFAULT_MONGO_HOST,
                  mongo_port=yapga.db.DEFAULT_MONGO_PORT):
    "List all of the change messages in a changes file."

    with yapga.db.get_db(dbname, mongo_host, mongo_port) as db:
        for change in yapga.db.all_changes(db):
            for msg in change.messages:
                print(msg)


@baker.command
def compare_reviewers(dbname,
                      mongo_host=yapga.db.DEFAULT_MONGO_HOST,
                      mongo_port=yapga.db.DEFAULT_MONGO_PORT,
                      filter_rate=0.0):
    """Heatmap showing how often reviewers review change owners.
    """
    import math
    import matplotlib.pyplot as plt

    filter_rate = float(filter_rate)

    # http://stackoverflow.com/questions/14391959/heatmap-in-matplotlib-with-pcolor

    with yapga.db.get_db(dbname, mongo_host, mongo_port) as db:
        reviews = dict(yapga.db.all_reviewers(db))
        changes = list(yapga.db.all_changes(db))

    owners = collections.defaultdict(lambda: 0)
    for change in changes:
        owners[change.owner.name] += 1

    owners = list(sorted(
        # Extract just the names from ...
        x[0] for x in

        # ...the first N (i.e. the people with the most
        # changes) of...
        itertools.islice(

            # ...owners dict sorted by number of changes.
            sorted(owners.items(),
                   key=lambda x: x[1],
                   reverse=True),
            math.ceil((1 - filter_rate) * len(owners)))))

    reviewers = collections.defaultdict(lambda: 0)
    for revs in reviews.values():
        for r in revs:
            reviewers[r.name] += 1

    reviewers = list(sorted(
        x[0] for x in
        itertools.islice(
            sorted(reviewers.items(),
                   key=lambda x: x[1],
                   reverse=True),
            math.ceil((1 - filter_rate) * len(reviewers)))))

    #owners = list(sorted(set(
    #    c.owner.name for c in changes)))
    #reviewers = list(sorted(set(
    #    r.name for revs in reviews.values() for r in revs)))

    if not owners:
        print('Owners list is empty. Aborting.')
        return

    if not reviewers:
        print('Reviewers list is empty. Aborting.')
        return

    # This is a matrix of reviewer to owner, where each cell is a
    # count of how many times a reviewer reviewed a particular owner
    data = np.zeros((len(reviewers), len(owners)))

    for change in changes:
        try:
            owner_idx = yapga.util.index_of(owners, change.owner.name)

            for reviewer in reviews.get(change.change_id, []):
                try:
                    reviewer_idx = yapga.util.index_of(reviewers, reviewer.name)
                    data[(reviewer_idx, owner_idx)] += 1
                except ValueError:
                    pass

        except ValueError:
            pass

    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.set_title('Reviewers vs. owners heatmap')
    ax.set_xlabel('Owner')
    ax.set_ylabel('Reviewer')
    ax.pcolormesh(data)

    def on_click(event):
        if event.xdata is None or event.ydata is None:
            return
        own_idx = math.floor(event.xdata)
        rev_idx = math.floor(event.ydata) + 1
        print('reviewer={}, owner={}'.format(
            reviewers[rev_idx],
            owners[own_idx]))

    fig.canvas.mpl_connect('button_press_event', on_click)

    plt.show()


@baker.command
def changes_vs_messages(dbname,
                        mongo_host=yapga.db.DEFAULT_MONGO_HOST,
                        mongo_port=yapga.db.DEFAULT_MONGO_PORT):
    """Scatter of #changes vs. #messages for a given user.
    """

    with yapga.db.get_db(dbname, mongo_host, mongo_port) as db:
        changes = list(yapga.db.all_changes(db))

    data = collections.defaultdict(lambda: [0, 0])
    for change in changes:
        data[change.owner.name][0] += 1
        for message in change.messages:
            if message.author is not None:
                data[message.author.name][1] += 1
            else:
                log.info('No author information for message {}'.format(
                    message.id))

    # Turn the data into a list of users, change counts, and review
    # counts
    names, change_counts, review_counts = zip(
        *((i[0], i[1][0], i[1][1])
          for i in data.items()))

    import matplotlib.pyplot as plt

    fig = plt.figure()
    p = fig.add_subplot(111)
    p.set_title('Changes vs. reviews')
    p.set_xlabel('# changes')
    p.set_ylabel('# review messages')

    p.scatter(change_counts,
              review_counts,
              picker=5)

    # When a point is clicked, show information about it.
    def onpick(event):
        print('==== User stats ====')
        for ind in event.ind:
            print('{}, reviews={} messages={}'.format(
                names[ind],
                change_counts[ind],
                review_counts[ind]))
        print('')
    fig.canvas.mpl_connect('pick_event', onpick)

    plt.show()
