from __future__ import (
    unicode_literals,
    absolute_import,
    print_function,
    division,
    )
import os
import unittest
import avb

import avb.utils

test_file_01 = os.path.join(os.path.dirname(__file__), 'test_files', 'test_file_01.avb')

result_dir = os.path.join(os.path.dirname(__file__), 'results')

if not os.path.exists(result_dir):
    os.makedirs(result_dir)

class TestRead(unittest.TestCase):

    def test_rewrite(self):
        with avb.open(test_file_01) as f:
            f.write(os.path.join(result_dir, 'rewrite.avb'))


if __name__ == "__main__":
    unittest.main()
