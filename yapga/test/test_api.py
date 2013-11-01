import os
import unittest

import yapga.util


def data_file_path(filename):
    own_dir = os.path.split(os.path.join(os.getcwd(), __file__))[0]
    data_dir = os.path.join(own_dir, 'data')
    return os.path.join(data_dir, filename)


class APITests(unittest.TestCase):
    def setUp(self):
        self.changes = list(
            yapga.util.load_changes(
                data_file_path('basic_changes.json')))

    def test_smoke_test(self):
        self.assertEqual(len(self.changes), 2)
