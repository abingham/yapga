import itertools

from yapga import changes, create_connection
import yapga.user_settings


def list_changes():
    conn = create_connection(yapga.user_settings.url,
                             yapga.user_settings.username,
                             yapga.user_settings.password)
    for c in itertools.islice(changes(conn), 100):
        print(c.data)


def list_all_revisions():
    conn = create_connection(yapga.user_settings.url,
                             #yapga.user_settings.username,
                             #yapga.user_settings.password
                             )
    for c in itertools.islice(changes(conn), 100):
        print('change-id:', c.id)

        for r in c.revisions:
            print(r.id, r.data)

if __name__ == '__main__':
    list_all_revisions()
