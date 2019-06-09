import unittest
import os

import linkthedots.functions as functions


class TestFunc(unittest.TestCase):
    def test_shrinkuser(self):
        # Assume
        original = '~/test'
        path = os.path.expanduser(original)

        # Action
        path = functions.shrinkuser(path)

        # Assert
        self.assertEqual(path, original)
