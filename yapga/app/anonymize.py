import json

import baker

import yapga.gerrit_api


@baker.command
def anonymize_changes(infile, outfile):
    with open(infile, 'rt') as f:
        changes = json.loads(f.read())

    name_map = {}
    email_map = {}

    next_name_id = 0
    next_email_id = 0

    def next_name():
        nonlocal next_name_id

        rslt = 'USER{}'.format(next_name_id)
        next_name_id += 1
        return rslt

    def next_email():
        nonlocal next_email_id

        rslt = 'ADDRESS{}@UNKNOWN.COM'.format(next_email_id)
        next_email_id += 1
        return rslt

    for change in changes:
        change = yapga.gerrit_api.Change(change)
        owner_name = change.owner.name
        if owner_name not in name_map:
            name_map[owner_name] = next_name()

        owner_email = change.owner.email
        if owner_email not in email_map:
            email_map[owner_email] = next_email()

    for change in changes:
        change = yapga.gerrit_api.Change(change)
        change.owner.name = name_map[change.owner.name]
        change.owner.email = email_map[change.owner.email]

    with open(outfile, 'wt') as f:
        json.dump(changes, f)
