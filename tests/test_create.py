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


def create_mastermob(f):
    edit_rate = 25

    tape_mob =  f.create.Composition(mob_type="SourceMob")
    tape_mob.descriptor = f.create.TapeDescriptor()
    tape_mob.descriptor.mob_kind = 2 # won't work without
    tape_mob.name = "Example Tape"
    tape_mob.length = 10368000

    track = f.create.Track()
    track.index = 1
    track.component = f.create.Timecode(edit_rate=edit_rate, media_kind='timecode')
    track.component.length = 10368000
    tape_mob.tracks.append(track)

    track = f.create.Track()
    track.index = 1
    track.component = f.create.SourceClip(edit_rate=edit_rate, media_kind='picture')
    track.component.length = 100
    track.filler_proxy = f.create.TrackRef(edit_rate=edit_rate, media_kind='picture')
    track.filler_proxy.length = 2147483647
    tape_mob.tracks.append(track)

    file_mob = f.create.Composition(mob_type="SourceMob")
    file_mob.descriptor = f.create.CDCIDescriptor()
    file_mob.descriptor.length = 100
    file_mob.descriptor.mob_kind = 1 # won't work without
    file_mob.length = 100
    track = f.create.Track()

    track.index = 1
    track.component = f.create.SourceClip(edit_rate=edit_rate, media_kind='picture')
    track.component.length = 100
    track.component.track_id = 1
    track.component.start_time = 25 * 60 * 60
    track.component.mob_id = tape_mob.mob_id
    track.filler_proxy = f.create.TrackRef(edit_rate=edit_rate, media_kind='picture')
    track.filler_proxy.length = 2147483647

    file_mob.tracks.append(track)

    mob = f.create.Composition(mob_type="MasterMob")
    mob.name = u"Clip1"

    track = f.create.Track()
    track.index = 1
    track.filler_proxy = f.create.TrackRef(edit_rate=edit_rate, media_kind='picture')
    track.filler_proxy.length = 2147483647

    clip = f.create.SourceClip(edit_rate=edit_rate, media_kind='picture')
    clip.length = 100
    clip.mob_id = file_mob.mob_id
    clip.track_id = 1
    track.component = clip
    mob.length = 100

    mob.tracks.append(track)

    f.content.add_mob(mob)
    f.content.add_mob(file_mob)
    f.content.add_mob(tape_mob)
    \
    return mob

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
            mob = create_mastermob(f)
            mob_id = mob.mob_id
            f.write(result_file)

        with avb.open(result_file) as f:
            mobs = list(f.content.mobs)
            mob = mobs[0]
            assert mob.name == u"Clip1"
            assert mob.mob_id == mob_id
            assert mob.mob_type == 'MasterMob'


    def test_create_sequence(self):
        result_file = os.path.join(result_dir, 'sequence.avb')
        with avb.open() as f:
            edit_rate = 25
            mob1 = create_mastermob(f)
            mob2 = create_mastermob(f)

            comp = f.create.Composition(mob_type="CompositionMob")

            comp.name = "Test Sequence"

            # timecode track
            track = f.create.Track()
            track.index = 1
            track.component = f.create.Timecode(edit_rate=edit_rate, media_kind='timecode')
            track.component.start = 90000
            track.component.fps = 25
            track.component.length = 500
            comp.tracks.append(track)

            # V1
            track = f.create.Track()
            track.index = 1
            track.filler_proxy = f.create.TrackRef(edit_rate=edit_rate, media_kind='picture')
            track.filler_proxy.length = 2147483647
            track.filler_proxy.relative_scope = 0
            track.filler_proxy.relative_track

            sequence = f.create.Sequence(edit_rate=edit_rate, media_kind='picture')
            sequence.components.append(f.create.Filler(edit_rate=edit_rate, media_kind='picture'))

            clip = f.create.SourceClip(edit_rate=edit_rate, media_kind='picture')
            clip.track_id = 1
            clip.start_time = 25
            clip.length = 50
            clip.mob_id = mob1.mob_id
            sequence.components.append(clip)

            fill = f.create.Filler(edit_rate=edit_rate, media_kind='picture')
            fill.length = 50
            sequence.components.append(fill)

            clip = f.create.SourceClip(edit_rate=edit_rate, media_kind='picture')
            clip.track_id = 1
            clip.start_time = 25
            clip.length = 50
            clip.mob_id = mob2.mob_id
            sequence.components.append(clip)

            sequence.components.append(f.create.Filler(edit_rate=edit_rate, media_kind='picture'))

            track.component = sequence
            comp.tracks.append(track)
            comp.length = sequence.length

            # A1
            track = f.create.Track()
            track.index = 1
            sequence = f.create.Sequence(edit_rate=edit_rate, media_kind='sound')
            fill = f.create.Filler(edit_rate=edit_rate, media_kind='sound')
            fill.length = comp.length
            sequence.components.append(fill)
            track.component = sequence
            comp.tracks.append(track)

            # A2
            track = f.create.Track()
            track.index = 2
            sequence = f.create.Sequence(edit_rate=edit_rate, media_kind='sound')
            fill = f.create.Filler(edit_rate=edit_rate, media_kind='sound')
            fill.length = comp.length
            sequence.components.append(fill)
            track.component = sequence
            comp.tracks.append(track)

            f.content.add_mob(comp)

            f.write(result_file)


if __name__ == "__main__":
    unittest.main()
