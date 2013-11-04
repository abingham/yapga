import os
import unittest

import yapga.util


def data_file_path(filename):
    own_dir = os.path.split(os.path.join(os.getcwd(), __file__))[0]
    data_dir = os.path.join(own_dir, 'data')
    return os.path.join(data_dir, filename)


simple_change_attributes = [
    'branch',
    'change_id',
    'created',
    'current_revision',
    'id',
    'kind',
    '_number',
    'project',
    '_sortkey',
    'status',
    'subject',
    'updated'
]


simple_revision_attributes = [
    '_number',
]


class APITests(unittest.TestCase):
    def setUp(self):
        self.changes = list(
            yapga.util.load_changes(
                data_file_path('basic_changes.json')))

    def test_smoke_test(self):
        """Just kicking the tires."""
        self.assertEqual(len(self.changes), 2)

    def test_changes(self):
        for change in self.changes:
            # TODO: messages
            # TODO: owner

            for name in simple_change_attributes:
                self.assertEqual(
                    getattr(change, name),
                    change.data[name])

    def test_revision_count(self):
        self.assertEqual(len(list(self.changes[0].revisions)), 2)
        self.assertEqual(len(list(self.changes[1].revisions)), 3)

    def test_revisions(self):
        # TODO: commit
        # TODO: files
        # fetch
        for change in self.changes:
            for revision in change.revisions:
                for name in simple_revision_attributes:
                    self.assertEqual(
                        getattr(revision, name),
                        revision.data[name])
