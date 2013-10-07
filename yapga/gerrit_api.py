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


def fetch_changes(conn, queries=None):
    """Generate a sequence of ChangeInfo structs (see: gerrit REST API
    documentation.)
    """
    if queries is None:
        queries = ['q=status:merged',
                   'o=ALL_REVISIONS',
                   'o=ALL_FILES',
                   'n=500']

    changes = conn.req(['changes'],
                       queries=queries)
    for c in changes:
        yield c

    while changes[-1].get('_more_changes', False):
        changes = conn.req(
            ['changes'],
            queries=queries + ['N={}'.format(changes[-1]['_sortkey'])])
        for c in changes:
            yield c


class JSONObject:
    def __init__(self, data):
        self.data = data

    def __getattr__(self, name):
        return self.data[name]


class Change:
    def __init__(self, data):
        self.data = data

    def __getattr__(self, name):
        return self.data[name]

    @property
    def revisions(self):
        revs = self.data.get('revisions', {})
        for rev_id, rev_data in revs.items():
            yield Revision(self.id, rev_id, rev_data)

    def __str__(self):
        return 'Change(id={})'.format(self.id)

    def __repr__(self):
        return str(self)


class Revision:
    def __init__(self, change_id, rev_id, data):
        self.change_id = change_id
        self.id = rev_id
        self.data = data

    def __getattr__(self, name):
        return self.data[name]

    def size(self):
        return sum([f.get('lines_inserted', 0) + f.get('lines_deleted', 0)
                    for f in self.data.get('files', {}).values()])
