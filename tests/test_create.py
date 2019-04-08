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
            edit_rate = 25

            tape_mob =  f.create.Composition(mob_type="SourceMob")
            tape_mob.descriptor = f.create.TapeDescriptor()
            tape_mob.name = "Example Tape"

            track = f.create.Track()
            track.index = 1
            track.component = f.create.SourceClip(edit_rate=edit_rate, media_kind='picture')
            track.component.length = 100
            track.filler_proxy = f.create.TrackRef(edit_rate=edit_rate, media_kind='picture')
            track.filler_proxy.length = 2147483647
            tape_mob.tracks.append(track)

            source_mob = f.create.Composition(mob_type="SourceMob")
            source_mob.descriptor = f.create.CDCIDescriptor()
            source_mob.descriptor.length = 100
            source_mob.length = 100
            track = f.create.Track()

            track.index = 1
            track.component = f.create.SourceClip(edit_rate=edit_rate, media_kind='picture')
            track.component.length = 100
            track.component.track_id = 1
            track.component.mob_id = tape_mob.mob_id
            track.filler_proxy = f.create.TrackRef(edit_rate=edit_rate, media_kind='picture')
            track.filler_proxy.length = 2147483647

            source_mob.tracks.append(track)

            mob = f.create.Composition(mob_type="MasterMob")
            mob.name = u"Clip1"
            mob_id = mob.mob_id

            track = f.create.Track()
            track.index = 1
            track.filler_proxy = f.create.TrackRef(edit_rate=edit_rate, media_kind='picture')
            track.filler_proxy.length = 2147483647

            clip = f.create.SourceClip(edit_rate=edit_rate, media_kind='picture')
            clip.length = 100
            clip.mob_id = source_mob.mob_id
            clip.track_id = 1

            track.component = clip
            mob.length = 100

            mob.tracks.append(track)

            f.content.add_mob(mob)
            f.content.add_mob(source_mob)
            f.content.add_mob(tape_mob)

            f.write(result_file)

        with avb.open(result_file) as f:
            mobs = list(f.content.mobs)
            mob = mobs[0]
            assert mob.name == u"Clip1"
            assert mob.mob_id == mob_id
            assert mob.mob_type == 'MasterMob'

if __name__ == "__main__":
    unittest.main()
