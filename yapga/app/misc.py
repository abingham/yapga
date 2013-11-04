import collections
import itertools
import logging

import baker
import numpy as np

import yapga.util


log = logging.getLogger('yapga')


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
    "Histogram of number of revision per change."
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
    "Simple histogram of change count by owners."
    counts = {}

    for change in yapga.util.load_changes(filename):
        o = change.owner.name
        counts[o] = counts.get(o, 0) + 1

    counts = sorted(counts.items(), key=lambda x: x[1])
    for c in counts:
        print((c[1] // 10) * '*', c[0])


@baker.command
def list_messages(filename):
    "List all of the change messages in a changes file."
    for change in yapga.util.load_changes(filename):
        print(list(change.messages))


@baker.command
def list_reviewers(filename):
    "List all of the reviewers in a reviews file."
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
        zip(set(c.owner.name for c in changes),
            itertools.count()))

    reviewer_map = dict(
        zip(set(r.name for revs in reviews.values() for r in revs),
            itertools.count()))

    data = np.zeros((len(reviewer_map), len(owner_map)))

    for change in changes:
        owner_idx = owner_map[change.owner.name]
        for reviewer in reviews.get(change.id, []):
            reviewer_idx = reviewer_map[reviewer.name]
            data[(reviewer_idx, owner_idx)] += 1

    import matplotlib.pyplot as plt
    fig, ax = plt.subplots()

    print('calculating heatmap...')
    ax.pcolor(data)
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


@baker.command
def changes_vs_messages(changes):
    """Scatter of #changes vs. #messages for a given user.
    """
    changes = list(yapga.util.load_changes(changes))

    data = collections.defaultdict(lambda: [0, 0])
    for change in changes:
        data[change.owner.name][0] += 1
        for message in change.messages:
            if message.author is not None:
                data[message.author.name][1] += 1
            else:
                log.info('No author information for message {}'.format(
                    message.id))

    import matplotlib.pyplot as plt
    plt.scatter([x[0] for x in data.values()],
                [x[1] for x in data.values()])
    plt.show()
