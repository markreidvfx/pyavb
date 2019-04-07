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


result_dir = os.path.join(os.path.dirname(__file__), 'results')

if not os.path.exists(result_dir):
    os.makedirs(result_dir)

class TestCreate(unittest.TestCase):

    def test_create_empty(self):
        result_file = os.path.join(result_dir, 'empty.avb')
        with avb.open() as f:
            f.write(result_file)

        with avb.open(result_file) as f:
            assert f.content.view_setting.name == u'Untitled'
            assert len(f.content.items) == 0

    def test_create_mastermob(self):
        result_file = os.path.join(result_dir, 'mastermob.avb')

        mob_id = None
        with avb.open() as f:
            mob = f.create.Composition(mob_type="MasterMob")
            mob.name = u"Clip1"
            mob_id = mob.mob_id
            f.content.add_mob(mob)

            f.write(result_file)

        with avb.open(result_file) as f:
            mobs = list(f.content.mobs)
            mob = mobs[0]
            assert mob.name == u"Clip1"
            assert mob.mob_id == mob_id
            assert mob.mob_type == 'MasterMob'

if __name__ == "__main__":
    unittest.main()
