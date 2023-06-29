from __future__ import (
    unicode_literals,
    absolute_import,
    print_function,
    division,
    )
import os
import unittest
import avb

from test_write import compare

test_file_01 = os.path.join(os.path.dirname(__file__), 'test_files', 'test_file_01.avb')

result_dir = os.path.join(os.path.dirname(__file__), 'results')

if not os.path.exists(result_dir):
    os.makedirs(result_dir)


class TestWrite(unittest.TestCase):

    def test_copy(self):
        result_file = os.path.join(result_dir, 'copy.avb')
        with avb.open(test_file_01) as a:
            with avb.open() as b:
                for mob in a.content.mobs:
                    new_mob = mob.copy(b)
                    b.content.add_mob(new_mob)
                b.write(result_file)

        with avb.open(test_file_01) as a:
            with avb.open(result_file) as b:
                b.content.build_mob_dict()
                for mob_a in a.content.mobs:
                    mob_b = b.content.mob_dict.get(mob_a.mob_id, None)
                    assert mob_b
                    compare(mob_a, mob_b)

if __name__ == "__main__":
    unittest.main()
