import itertools
import json
import logging

import baker

import yapga
import yapga.db
import yapga.util


log = logging.getLogger('yapga')


@baker.command
def fetch(url,
          dbname,
          mongo_host=yapga.db.DEFAULT_MONGO_HOST,
          mongo_port=yapga.db.DEFAULT_MONGO_PORT,
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
    with yapga.db.get_db(dbname,
                           mongo_host,
                           mongo_port) as db:
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

        try:
            for chunk in (list(c) for c in chunks):
                if not chunk:
                    break
                for change in chunk:
                    yapga.db.insert_change(db, change)
        except Exception:
            log.exception(
                'Error fetching results. Partial results saved.')


@baker.command
def fetch_reviewers(url,
                    dbname,
                    mongo_host=yapga.db.DEFAULT_MONGO_HOST,
                    mongo_port=yapga.db.DEFAULT_MONGO_PORT,
                    username=None,
                    password=None):
    """Fetch all reviewers for the changes in `changes` collection from `url`. The
    results are written to the `reviewers` collection as a json map from change-id to
    review-list.
    """

    with yapga.db.get_db(dbname,
                         mongo_host,
                         mongo_port) as db:
        conn = yapga.create_connection(url, username, password)

        for c in yapga.db.all_changes(db):
            try:
                if yapga.util.is_empty(
                        yapga.db.get_reviewers(db, c.change_id)):
                    print('Fetching reviewers for change {}'.format(c.change_id))
                    yapga.db.insert_reviewers(
                        db,
                        c.change_id,
                        yapga.fetch_reviewers(conn, c.change_id))
                else:
                    print('Reviews already found for {}'.format(c.change_id))
            except Exception:
                log.exception(
                    'Error fetching reviewers for change {}'.format(c.change_id))
