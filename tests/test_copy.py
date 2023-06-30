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

    def test_copy_mastermob_depends(self):
        result_file = os.path.join(result_dir, 'copy_mastermobs.avb')

        mob_ids = set()
        with avb.open(test_file_01) as a:
            with avb.open() as b:
                mobs = {}
                for mob in a.content.mastermobs():
                    mobs[mob.mob_id] = mob
                    for m in mob.dependant_mobs():
                        mobs[m.mob_id] = m

                for mob in mobs.values():
                    mob_ids.add(mob.mob_id)
                    new_mob = mob.copy(b)
                    b.content.add_mob(new_mob)


                b.write(result_file)

        with avb.open(test_file_01) as a:
            with avb.open(result_file) as b:
                b.content.build_mob_dict()
                a.content.build_mob_dict()
                for mob_id in mob_ids:
                    mob_a = a.content.mob_dict.get(mob_id, None)
                    mob_b = b.content.mob_dict.get(mob_id, None)
                    compare(mob_a, mob_b)

    def test_copy_compositionmobs(self):
        result_file = os.path.join(result_dir, 'copy_compositionmob.avb')

        mob_ids = set()
        with avb.open(test_file_01) as a:
            with avb.open() as b:

                mobs = {}
                for mob in a.content.compositionmobs():
                    mobs[mob.mob_id] = mob
                    for m in mob.dependant_mobs():
                        mobs[m.mob_id] = m

                for mob in mobs.values():
                    mob_ids.add(mob.mob_id)
                    new_mob = mob.copy(b)
                    b.content.add_mob(new_mob)


                b.write(result_file)

        with avb.open(test_file_01) as a:
            with avb.open(result_file) as b:
                b.content.build_mob_dict()
                a.content.build_mob_dict()
                for mob_id in mob_ids:
                    mob_a = a.content.mob_dict.get(mob_id, None)
                    mob_b = b.content.mob_dict.get(mob_id, None)
                    compare(mob_a, mob_b)

if __name__ == "__main__":
    unittest.main()
