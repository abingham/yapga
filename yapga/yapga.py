import json
import logging
import urllib.request

import yapga.user_settings


logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger()

auth_handler = urllib.request.HTTPDigestAuthHandler()
auth_handler.add_password(realm='Gerrit Code Review',
                          uri=yapga.user_settings.url,
                          user=yapga.user_settings.username,
                          passwd=yapga.user_settings.password)
opener = urllib.request.build_opener(auth_handler)

# ...and install it globally so it can be used with urlopen.
urllib.request.install_opener(opener)


class Connection:
    def __init__(self, url):
        self.url = url

    def changes(self, queries=None):
        if queries is None:
            queries = ['q=status:merged',
                       'o=CURRENT_REVISION',
                       'n=100']

        rslt = []
        changes = self.req(['changes'], queries=queries)

        rslt.extend([Change(c) for c in changes])
        while changes[-1].get('_more_changes', False):
            changes = self.req(
                ['changes'],
                queries=queries + ['N={}'.format(changes[-1]['_sortkey'])])
            rslt.extend([Change(c) for c in changes])

        return rslt

    def req(self, path, queries=None):
        url = '{}/a/{}/'.format(self.url,
                             '/'.join(path))
        if queries:
            url += '?{}'.format('&'.join(queries))

        log.info('request url: {}'.format(url))

        req = urllib.request.urlopen(url)
        data = req.read()
        data = data[4:]  # strip "magic" anti-XSSI header
        data = data.decode('utf-8')
        return json.loads(data)


class JSONObject:
    def __init__(self, data):
        self.data = data

    def __getattr__(self, name):
        return self.data[name]


class Change(JSONObject):
    @property
    def revisions(self):
        return [Revision(r) for r in self.data['revisions']]


class Revision(JSONObject):
    pass

def list_changes():
    conn = Connection(yapga.user_settings.url)
    for c in conn.changes():
        print(c.id)


def list_all_revisions():
    conn = Connection(yapga.user_settings.url)
    for c in conn.changes:
        print('change-id:', c.id)

        for r in c.revisions:
            pass

list_changes()
