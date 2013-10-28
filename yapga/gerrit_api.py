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


def fetch_reviewers(conn, change_id):
    return conn.req(['changes', change_id, 'reviewers'])

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

    @property
    def messages(self):
        msgs = self.data.get('messages', [])
        for msg in msgs:
            yield ChangeMessage(msg)

    @property
    def owner(self):
        return Account(self.data['owner'])

    def __str__(self):
        return 'Change(id={})'.format(self.id)

    def __repr__(self):
        return str(self)


class Account:
    def __init__(self, data):
        self.data = data

    @property
    def id(self):
        return self.data['_account_id']

    @property
    def name(self):
        return self.data.get('name', 'UNKNOWN')

    @property
    def email(self):
        return self.data.get('email', 'UNKNOWN')

    def __repr__(self):
        return 'Account(name="{}", email="{}")'.format(
            self.name, self.email)

    def __str__(self):
        return repr(self)


class Reviewer(Account):
    @property
    def kind(self):
        return self.data.get('kind', 'UNKNOWN')

    @property
    def approvals(self):
        return self.data.get('approvals', {})


class ChangeMessage:
    def __init__(self, data):
        self.data = data
        self.id = self.data.get('id', 'UNKNOWN')

        try:
            self.author = Account(self.data['author'])
        except KeyError:
            self.author = None

        self.date = self.data['data']
        self.message = self.data['message']
        self.revision_number = self.data.get('_revision_number', 0)


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
