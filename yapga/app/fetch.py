import itertools
import json
import logging

import baker

import yapga
import yapga.util


log = logging.getLogger('yapga')


@baker.command
def fetch(url,
          filename,
          username=None,
          password=None,
          count=None,
          batch_size=500,
          start_at=None,
          status='merged'):
    """Fetch up to `count` changes from the gerrit server at `url`,
    grabbing them in batches of `batch_size`. The results are saved as
    a JSON list of `ChangeInfo` objects into `filename`.

    If `username` and `password` are supplied, then they are used for
    digest authentication with the server.
    """
    queries = ['q=status:{}'.format(status),
               'o=ALL_REVISIONS',
               'o=ALL_FILES',
               'o=ALL_COMMITS',
               'o=MESSAGES',
               'n={}'.format(batch_size)]

    if start_at is not None:
        queries.append('N={}'.format(start_at))

    if count is not None:
        count = int(count)

    conn = yapga.create_connection(url, username, password)
    chunks = yapga.util.chunks(
        itertools.islice(yapga.fetch_changes(conn, queries=queries),
                         count),
        batch_size)

    changes = []
    try:
        for chunk in (list(c) for c in chunks):
            if not chunk:
                break
            changes.extend(chunk)
    except Exception:
        log.exception(
            'Error fetching results. Partial results '
            'will be saved to {}'.format(
                filename))
    finally:
        log.info('{} changes retrieved.'.format(len(changes)))
        if changes:
            with open(filename, 'w') as f:
                f.write(json.dumps(changes))


@baker.command
def fetch_reviewers(change_file,
                    url,
                    filename,
                    username=None,
                    password=None):
    """Fetch all reviewers for the changes in `change_file` from `url`. The
    results are written to `filename` as a json map from change-id to
    review-list.
    """

    conn = yapga.create_connection(url, username, password)

    data = {}
    for c in yapga.util.load_changes(change_file):
        try:
            data[c.id] = yapga.fetch_reviewers(conn, c.id)
        except Exception:
            log.exception(
                'Error fetching reviewers for change {}'.format(c.id))

    with open(filename, 'w') as f:
        f.write(json.dumps(data))
