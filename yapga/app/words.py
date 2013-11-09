import collections
import itertools
import re

import baker

import yapga.util


skip_words = list(itertools.chain(
    map(str.upper,
        [
            'Patch',
            'Set',
            'the',
            'a',
            'an',
            'to',
            'Code-Review+1',
            'Code-Review+2',
            'Verified+1',
            'Verfied',
        ]),
    list(map(''.join,
             itertools.product(map(str, range(10)),
                               ':.')))))

def filter_messages(messages):
    for m in messages:
        if re.match('Uploaded patch set \d+.', m):
            print(m)
            continue
        yield m

@baker.command
def word_count(changes, count=20):
    changes = list(yapga.util.load_changes(changes))
    word_counts = collections.defaultdict(lambda: 0)
    messages = filter_messages(m.message
                               for c in changes
                               for m in c.messages)

    for word in filter(lambda x: x.upper() not in skip_words,
                       (w for m in messages
                          for w in m.split())):
        word_counts[word] += 1

    words = sorted(word_counts.items(), key=lambda x: x[1])
    count = min(count, len(words))

    import matplotlib.pyplot as plt
    plt.bar(range(count),
            [w[1] for w in words[-count:]])
    plt.xticks(range(count),
               [w[0] for w in words[-count:]],
               rotation='vertical')
    plt.show()

    # for word, count in sorted(word_counts.items(), key=lambda x: x[1]):
    #     print(count // 1000 * '*', count, word)
    #     # print(count, '\t', word)


@baker.command
def random_message(changes, size=100):
    import nltk

    changes = list(yapga.util.load_changes(changes))
    messages = (m.message for c in changes for m in c.messages)
    text = nltk.Text([nltk.word_tokenize(msg) for msg in messages])
    text.generate(100)
