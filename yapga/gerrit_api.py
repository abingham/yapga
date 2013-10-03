import json
import logging
import urllib.request


logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger()


class Connection:
    def __init__(self, uri, opener):
        self.uri = uri
        self.opener = opener

    def req(self, path, queries=None):
        url = '{}/{}/'.format(self.uri,
                             '/'.join(path))
        if queries:
            url += '?{}'.format('&'.join(queries))

        log.info('request url: {}'.format(url))

        req = self.opener.open(url)
        data = req.read()
        data = data[4:]  # strip "magic" anti-XSSI header
        data = data.decode('utf-8')
        return json.loads(data)


def create_connection(uri, username=None, password=None):
    handlers = []
    if username is not None:
        # Create an auth-handler for our user
        auth_handler = urllib.request.HTTPDigestAuthHandler()
        auth_handler.add_password(realm='Gerrit Code Review',
                                  uri=uri,
                                  user=username,
                                  passwd=password)
        handlers.append(auth_handler)

    opener = urllib.request.build_opener(*handlers)
    return Connection(uri, opener)


class JSONObject:
    def __init__(self, data):
        self.data = data

    def __getattr__(self, name):
        return self.data[name]


class Change:
    def __init__(self, conn, data):
        self.conn = conn
        self.data = data

    def __getattr__(self, name):
        return self.data[name]

    @property
    def revisions(self):
        revs = self.data.get('revisions', {})
        for rev_id, rev_data in revs.items():
            yield Revision(self.conn, self.id, rev_id, rev_data)

    def __str__(self):
        return 'Change(id={})'.format(self.id)

    def __repr__(self):
        return str(self)


def changes(conn, queries=None, batch_size=100):
    if queries is None:
        queries = ['q=status:merged',
                   'o=ALL_REVISIONS',
                   'o=ALL_FILES',
                   'n={}'.format(batch_size)]

    changes = conn.req(['changes'],
                       queries=queries)
    for c in changes:
        yield Change(conn, c)

    while changes[-1].get('_more_changes', False):
        changes = conn.req(
            ['changes'],
            queries=queries + ['N={}'.format(changes[-1]['_sortkey'])])
        for c in changes:
            yield Change(conn, c)


class Revision:
    def __init__(self, conn, change_id, rev_id, data):
        self.conn = conn
        self.change_id = change_id
        self.id = rev_id
        self.data = data

    def __getattr__(self, name):
        return self.data[name]

    def size(self):
        return sum([f.get('lines_inserted', 0) + f.get('lines_deleted', 0)
                    for f in self.files.values()])
