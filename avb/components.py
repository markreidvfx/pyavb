from __future__ import (
    unicode_literals,
    absolute_import,
    print_function,
    division,
    )

from . import core
from . import utils

from . utils import (
    read_byte,
    read_s16le,
    read_u16le,
    read_u32le,
    read_s32le,
    read_string,
    read_exp10_encoded_float,
    read_object_ref,
    read_datetime,
    peek_data
)

from . import mobid

class Component(core.AVBObject):
    def read(self, f):
        tag = read_byte(f)
        version = read_byte(f)

        assert tag == 0x02
        assert version == 0x03

        l_bob = read_u32le(f)
        r_bob = read_u32le(f)

        self.media_kind_id = read_s16le(f)
        self.edit_rate = read_exp10_encoded_float(f)
        self.name = read_string(f)
        self.effect_id = read_string(f)

        self.attribute_ref = read_object_ref(self.root, f)
        self.session_ref = read_object_ref(self.root, f)

        self.precomputed = read_u32le(f)

        tag = read_byte(f)
        version = read_byte(f)

        assert tag == 0x01
        assert version == 0x01

        tag = read_byte(f)
        assert tag == 72

        self.param_list = read_object_ref(self.root, f)

        self.length = 0

    @property
    def media_kind(self):
        if self.media_kind_id   == 0:
            return None
        elif self.media_kind_id   == 1:
            return "picture"
        elif self.media_kind_id == 2:
            return "sound"
        elif self.media_kind_id == 3:
            return "timecode"
        elif self.media_kind_id == 4:
            return "edgecode"
        elif self.media_kind_id == 5:
            return "attribute"
        elif self.media_kind_id == 6:
            return 'effectdata'
        elif self.media_kind_id == 7:
            return 'descriptive meatadata'
        else:
            return "unknown%d" % self.media_kind_id

@utils.register_class
class Sequence(Component):
    class_id = "SEQU"

    def read(self, f):
        super(Sequence, self).read(f)
        tag = read_byte(f)
        version = read_byte(f)

        assert tag == 0x02
        assert version == 0x03

        count = read_u32le(f)
        self.component_refs = []
        for i in range(count):
            ref = read_object_ref(self.root, f)
            # print ref
            self.component_refs.append(ref)

        tag = read_byte(f)
        assert tag == 0x03

    def components(self):
        for ref in self.component_refs:
            yield ref.value

@utils.register_class
class RepSet(Component):
    class_id = 'RSET'
    def read(self, f):
        super(RepSet, self).read(f)
        tag = read_byte(f)
        version = read_byte(f)

        assert tag == 0x02
        assert version == 0x08

        #TODO: rest

class Clip(Component):
    def read(self, f):
        super(Clip, self).read(f)
        tag = read_byte(f)
        version = read_byte(f)
        # print self, "0x%02X" % tag, "0x%02X" % version
        assert tag == 0x02
        assert version == 0x01
        self.length = read_u32le(f)

@utils.register_class
class SourceClip(Clip):
    class_id = 'SCLP'
    def read(self, f):
        super(SourceClip, self).read(f)
        tag = read_byte(f)
        version = read_byte(f)

        assert tag == 0x02
        assert version == 0x03

        mob_id_hi = read_s32le(f)
        mob_id_lo = read_s32le(f)
        self.track_id = read_s16le(f)
        self.start_time = read_s32le(f)
        self.mob_id = mobid.read_mob_id(f)

        tag = read_byte(f)
        assert tag == 0x03

@utils.register_class
class Timecode(Clip):
    class_id = 'TCCP'

@utils.register_class
class Edgecode(Clip):
    class_id = 'ECCP'

@utils.register_class
class TrackRef(Clip):
    class_id = 'TRKR'

@utils.register_class
class ParamClip(Clip):
    class_id = 'PRCL'

@utils.register_class
class Filler(Clip):
    class_id = 'FILL'

    def read(self, f):
        super(Filler, self).read(f)
        tag = read_byte(f)
        version = read_byte(f)
        end_tag = read_byte(f)

        assert tag == 0x02
        assert version == 0x01
        assert end_tag == 0x03

class Track(object):
    def __init__(self):
        self.flags = None
        self.index = None
        self.lock_number = None
        self.refs = []

    @property
    def segment(self):
        for item in self.refs:
            obj = item.value
            if isinstance(obj, Component):
                return obj

class TrackGroup(Component):

    def read(self, f):
        super(TrackGroup, self).read(f)

        tag = read_byte(f)
        version = read_byte(f)

        assert tag == 0x02
        assert version == 0x08

        mode = read_byte(f)
        self.length = read_s32le(f)
        num_scalars = read_s32le(f)
        # print mode, self.length, num_scalars

        # print peek_data(f).encode("hex")

        track_count = read_s32le(f)
        # print  "track count :", track_count, 'pos:', f.tell()
        self.tracks = []

        # really annoying tracks can have differnt lenghts!!

        has_tracks = True
        for i in range(track_count):
            track = Track()

            track.flags = read_u16le(f)
            track.index = i + 1
            if track.flags != 4:
                track.index = read_s16le(f)

            if track.flags == 0 and track.index == 0:
                has_tracks = False
                break

            # print "{0:016b}".format(track.flags)
            # print "index: %04d" % track.index, "flags 0x%04X" % track.flags, track.flags
            ref_count = 1

            if track.flags in (13, 21, 517,):
                ref_count = 2
            elif track.flags in (29, 519, 525, 533,  ):
                ref_count = 3
            elif track.flags in (541, 527):
                ref_count = 4
            elif track.flags in (543,):
                ref_count = 5

            for j in range(ref_count):
                ref = read_object_ref(self.root, f)
                track.refs.append(ref)

            # for ref in track.refs:
            #     print "  ", ref

            self.tracks.append(track)

        tag = read_byte(f)
        version = read_byte(f)
        # print self.tracks, "%02X" % tag
        assert tag == 0x01
        assert version == 0x01

        for i in range(track_count):
            tag = read_byte(f)
            assert tag == 69
            lock =  read_s16le(f)
            if has_tracks:
                self.tracks[i].lock_number = lock

@utils.register_class
class CaptureMask(TrackGroup):
    class_id = 'MASK'

@utils.register_class
class TrackEffect(TrackGroup):
    class_id = 'TKFX'

@utils.register_class
class MotionEffect(TrackGroup):
    class_id = 'SPED'

# should inherent TrackGroup??
@utils.register_class
class TransistionEffect(Component):
    class_id = 'TNFX'

# should inherent TrackGroup??
@utils.register_class
class PanVolumeEffect(Component):
    class_id = 'PVOL'

# should inherent TrackGroup??
@utils.register_class
class Selector(Component):
    class_id = 'SLCT'

@utils.register_class
class Composition(TrackGroup):
    class_id = 'CMPO'

    def read(self, f):
        super(Composition, self).read(f)
        tag = read_byte(f)
        version = read_byte(f)
        assert tag == 0x02
        assert version == 0x02

        mob_id_hi = read_s32le(f)
        mob_id_lo = read_s32le(f)
        last_modified = read_s32le(f)

        self.mob_type_id = read_byte(f)
        self.usage_code =  read_s32le(f)
        self.descriptor = read_object_ref(self.root, f)

        tag = read_byte(f)
        version = read_byte(f)
        assert tag == 0x01
        assert version == 0x01

        tag = read_byte(f)
        assert tag == 71

        creation_time = read_datetime(f)
        self.mob_id = mobid.read_mob_id(f)

        assert read_byte(f) == 0x03

    @property
    def mob_type(self):
        if self.mob_type_id == 1:
            return "CompositionMob"
        elif self.mob_type_id == 2:
            return "MasterMob"
        elif self.mob_type_id == 3:
            return "SourceMob"
        else:
            raise ValueError("Unknown mob type id: %d" % self.mob_type_id)
