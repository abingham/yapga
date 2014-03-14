import collections.abc
import json

import baker

# from yapga.util import open_file


def json_transform(obj, t):
    """Walk OBJ as a mapping or sequence, calling T with each
    key-value mapping and replacing the values in the data structure
    with the return values.
    """
    if isinstance(obj, str):
        return

    if isinstance(obj, collections.abc.Mapping):
        for k, v in obj.items():
            obj[k] = t(k, v)
            json_transform(obj[k], t)

    elif isinstance(obj, collections.abc.Sequence):
        for x in obj:
            json_transform(x, t)


class Replacer:
    """A callable that fills in TEMPLATE with increasing integer
    values each time it's called.
    """
    def __init__(self, template):
        self.template = template
        self.counter = 0

    def __call__(self):
        self.counter += 1
        return self.template.format(self.counter)


@baker.command
def anonymize_changes(infile, outfile):
    """Read the changes from INFILE, anonymize names and email
    addresses, and write the results to OUTFILE.
    """
    with open_file(infile, 'rt') as f:
        changes = json.loads(f.read())

    name_map = collections.defaultdict(
        Replacer('UNKNOWN_{}'))
    mail_map = collections.defaultdict(
        Replacer('UNKNOWN_{}@UNKNOWN.UNK'))

    def anon(key, value):
        if not isinstance(value, str):
            return value

        if key == 'email':
            return mail_map[value]

        if key == 'name':
            return name_map[value]

        return value

    def anon_test(k, v):
        rslt = anon(k, v)
        return rslt

    json_transform(changes, anon_test)

    with open_file(outfile, 'wt') as f:
        json.dump(changes, f)
