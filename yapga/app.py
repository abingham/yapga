import itertools

import baker

from yapga import changes, create_connection


@baker.command
def list_changes(url, username=None, password=None):
    conn = create_connection(url,
                             username,
                             password)
    for c in itertools.islice(changes(conn), 100):
        print(c.data)


@baker.command(default=True)
def list_all_revisions(url, username=None, password=None):
    conn = create_connection(url,
                             username,
                             password)

    for c in itertools.islice(changes(conn), 100):
        print('change-id:', c.id)

        for r in c.revisions:
            print(r.id, r.data)

if __name__ == '__main__':
    baker.run()
