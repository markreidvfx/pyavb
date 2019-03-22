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

class TestRead(unittest.TestCase):

    def test_basic(self):
        with avb.open(test_file_01) as f:

            for item in f.content.mobs:
                pass
                # print(item)

    def test_read_all_known_classes(self):
        with avb.open(test_file_01) as f:
            for i, chunk in enumerate(f.chunks()):
                if chunk.class_id in  avb.utils.AVBClaseID_dict:

                    item = f.read_object(i)
                    # print(item)


if __name__ == "__main__":
    unittest.main()
