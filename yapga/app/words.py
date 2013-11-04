import collections
import itertools

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


@baker.command
def word_count(changes):
    changes = list(yapga.util.load_changes(changes))
    word_counts = collections.defaultdict(lambda: 0)
    for word in filter(lambda x: x.upper() not in skip_words,
                       (w for c in changes
                        for m in c.messages
                        for w in m.message.split())):
        word_counts[word] += 1
    for word, count in sorted(word_counts.items(), key=lambda x: x[1]):
        print(count // 1000 * '*', count, word)
        # print(count, '\t', word)


@baker.command
def random_message(changes, size=100):
    import nltk

    changes = list(yapga.util.load_changes(changes))
    messages = (m.message for c in changes for m in c.messages)
    text = nltk.Text([nltk.word_tokenize(msg) for msg in messages])
    text.generate(100)