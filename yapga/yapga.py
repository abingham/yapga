import json
import logging
import urllib.request


logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger()


class Connection:
    def __init__(self, uri, username, password):
        self.uri = uri
        self.username = username
        self.password = password

        # Create an auth-handler for our user
        auth_handler = urllib.request.HTTPDigestAuthHandler()
        auth_handler.add_password(realm='Gerrit Code Review',
                                  uri=uri,
                                  user=username,
                                  passwd=password)
        self.opener = urllib.request.build_opener(auth_handler)

    def req(self, path, queries=None):
        url = '{}/a/{}/'.format(self.uri,
                             '/'.join(path))
        if queries:
            url += '?{}'.format('&'.join(queries))

        log.info('request url: {}'.format(url))

        req = self.opener.open(url)
        data = req.read()
        data = data[4:]  # strip "magic" anti-XSSI header
        data = data.decode('utf-8')
        return json.loads(data)


def create_connection(uri, username, password):
    return Connection(uri, username, password)


class JSONObject:
    def __init__(self, data):
        self.data = data

    def __getattr__(self, name):
        return self.data[name]


class Change(JSONObject):
    @property
    def revisions(self):
        return [Revision(r) for r in self.data.get('revisions', [])]

    def __str__(self):
        return 'Change(id={})'.format(self.id)

    def __repr__(self):
        return str(self)

def changes(conn, queries=None):
    if queries is None:
        queries = ['q=status:merged',
                   'o=ALL_REVISIONS',
                   'o=ALL_COMMITS',
                   'n=100']

    rslt = []
    changes = conn.req(['changes'], queries=queries)

    rslt.extend([Change(c) for c in changes])
    while changes[-1].get('_more_changes', False):
        changes = conn.req(
            ['changes'],
            queries=queries + ['N={}'.format(changes[-1]['_sortkey'])])
        rslt.extend([Change(c) for c in changes])

    return rslt


class Revision(JSONObject):
    pass


def list_changes():
    import yapga.user_settings
    conn = Connection(yapga.user_settings.url,
                      yapga.user_settings.username,
                      yapga.user_settings.password)
    for c in changes(conn):
        if len(c.data['revisions']) == 1:
            print(c)
            return


def list_all_revisions():
    conn = Connection(yapga.user_settings.url)
    for c in conn.changes():
        print('change-id:', c.id)

        for r in c.revisions:
            print(r)

if __name__ == '__main__':
    list_changes()
