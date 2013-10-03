from yapga import create_connection
import yapga.user_settings


# objective: compare length of initial revision with number of
# revisions
def revisions_per_length():
    conn = create_connection(url, username, password)
    for change in conn.changes():
        for rev in change.revisions()[0]:
            pass
