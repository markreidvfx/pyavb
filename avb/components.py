from __future__ import (
    unicode_literals,
    absolute_import,
    print_function,
    division,
    )

from . import core
from .core import AVBProperty
from . import utils
from . import mobid

from . utils import (
    read_byte,
    read_s8,
    read_bool,
    read_s16le,
    read_u16le,
    read_u32le,
    read_s32le,
    read_string,
    read_doublele,
    read_exp10_encoded_float,
    read_object_ref,
    read_datetime,
    iter_ext,
    read_assert_tag,
    peek_data
)



class Component(core.AVBObject):
    class_id = b'COMP'
    properties = [
        AVBProperty('left_bob',      '__OMFI:CPNT:LeftBob',    'reference'),
        AVBProperty('right_bob',     '__OMFI:CPNT:RightBob',   'reference'),
        AVBProperty('media_kind_id', 'OMFI:CPNT:TrackKind',    'int16'),
        AVBProperty('edit_rate',     'EdRate',                 'fexp10'),
        AVBProperty('name',          'OMFI:CPNT:Name',         'string'),
        AVBProperty('effect_id',     'OMFI:CPNT:EffectID',     'string'),
        AVBProperty('attributes',    'OMFI:CPNT:Attributes',   'reference'),
        AVBProperty('session_attrs', 'OMFI:CPNT:SessionAttrs', 'reference'),
        AVBProperty('precomputed',   'OMFI:CPNT:Precomputed',  'reference'),
        AVBProperty('param_list',    'OMFI:CPNT:ParamList',    'reference'),
    ]

    def read(self, f):
        tag = read_byte(f)
        version = read_byte(f)

        assert tag == 0x02
        assert version == 0x03

        # bob == bytes of binary or bag of bits?
        self.left_bob =  read_object_ref(self.root, f)
        self.right_bob =  read_object_ref(self.root, f)

        self.media_kind_id = read_s16le(f)
        self.edit_rate = read_exp10_encoded_float(f)
        self.name = read_string(f)
        self.effect_id = read_string(f)

        self.attribute_ref = read_object_ref(self.root, f)
        self.session_ref = read_object_ref(self.root, f)

        self.precomputed = read_object_ref(self.root, f)

        self.param_list = None
        for tag in iter_ext(f):

            if tag == 0x01:
                read_assert_tag(f, 72)
                self.param_list = read_object_ref(self.root, f)
            else:
                raise ValueError("%s: unknown ext tag 0x%02X %d" % (str(self.class_id), tag,tag))

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
            return 'DescriptiveMetadata'
        else:
            return "unknown%d" % self.media_kind_id

@utils.register_class
class Sequence(Component):
    class_id = b"SEQU"
    properties = Component.properties + [
        AVBProperty('components_refs', 'OMFI:SEQU:Sequence', 'ref_list'),
    ]

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

class Clip(Component):
    class_id = b'CLIP'
    properties = Component.properties + [
        AVBProperty('length', 'OMFI:CLIP:Length', 'int32'),
    ]
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
    class_id = b'SCLP'
    properties = Clip.properties + [
        AVBProperty('track_id',   'OMFI:SCLP:SourceTrack',     'int16'),
        AVBProperty('start_time', 'OMFI:SCLP:SourcePosition',  'int32'),
        AVBProperty('mob_id',     'MobID',                     'MobID'),
    ]

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

        # null mobid
        if mob_id_hi == 0 and mob_id_lo == 0:
            self.mob_id = mobid.MobID()

        tag = read_byte(f)
        assert tag == 0x03

@utils.register_class
class Timecode(Clip):
    class_id = b'TCCP'
    properties = Clip.properties + [
        AVBProperty('flags', 'OMFI:TCCP:Flags',   'int32'),
        AVBProperty('fps',   'OMFI:TCCP:FPS',     'int32'),
        AVBProperty('start', 'OMFI:TCCP:StartTC', 'int32'),
    ]

    def read(self, f):
        super(Timecode, self).read(f)
        tag = read_byte(f)
        version = read_byte(f)

        assert tag == 0x02
        assert version == 0x01

        # drop ??
        self.flags = read_u32le(f)
        self.fps = read_u16le(f)

        # unused
        f.read(6)

        self.start = read_u32le(f)
        tag = read_byte(f)

        assert tag == 0x03

@utils.register_class
class Edgecode(Clip):
    class_id = b'ECCP'
    properties = Clip.properties + [
        AVBProperty('header',      'OMFI:ECCP:Header',      'bytes'),
        AVBProperty('film_kind',   'OMFI:ECCP:FilmKind',   'uint8'),
        AVBProperty('code_format', 'OMFI:ECCP:CodeFormat', 'uint8'),
        AVBProperty('base_perf',   'OMFI:ECCP:BasePerf',   'uint16'),
        AVBProperty('start_ec',    'OMFI:ECCP:StartEC',    'int32'),
    ]
    def read(self, f):
        super(Edgecode, self).read(f)
        # print("??", peek_data(f).encode("hex"))s
        tag = read_byte(f)
        version = read_byte(f)

        assert tag == 0x02
        assert version == 0x01

        self.header = bytearray(f.read(8))
        self.film_kind = read_byte(f)
        self.code_format =  read_byte(f)
        self.base_perf = read_u16le(f)
        unused_a  = read_u32le(f)
        self.start_ec = read_s32le(f)

        tag = read_byte(f)
        assert tag == 0x03

@utils.register_class
class TrackRef(Clip):
    class_id = b'TRKR'
    properties = Clip.properties + [
        AVBProperty('relative_scope', 'OMFI:TRKR:RelativeScope', 'int16'),
        AVBProperty('relative_track', 'OMFI:TRKR:RelativeTrack', 'int16'),
    ]
    def read(self, f):
        super(TrackRef, self).read(f)
        # print(peek_data(f).encode("hex"))
        tag = read_byte(f)
        version = read_byte(f)

        assert tag == 0x02
        assert version == 0x01

        self.relative_scope = read_s16le(f)
        self.relative_track = read_s16le(f)

        tag = read_byte(f)
        assert tag == 0x03

CP_TYPE_INT = 1
CP_TYPE_DOUBLE = 2

class ControlPoint(core.AVBObject):
    properties = [
        AVBProperty('offset',    'OMFI:PRCL:Offset',     'rational'),
        AVBProperty('timescale', 'OMFI:PRCL:TimeScale',  'int32'),
        AVBProperty('value',     'OMFI:PRCL:Value',      'number'), # int or double
        AVBProperty('pp',        'OMFI:PRCL:InterpKind', 'list'),
    ]

    def __init__(self, root):
        super(ControlPoint, self).__init__(root)
        self.pp = []

# not sure hwat PP's stands for
class PerPoint(core.AVBObject):
    properties = [
        AVBProperty('code',  'OMFI:PRCL:PPCode',  'int16'),
        AVBProperty('type',  'OMFI:PRCL:PPType',  'int16'),
        AVBProperty('value', 'OMFI:PRCL:PPValue', 'number'), # int or double
    ]

@utils.register_class
class ParamClip(Clip):
    class_id = b'PRCL'
    properties = Clip.properties + [
        AVBProperty('interp_kind',    'OMFI:PRCL:InterpKind',    'int32'),
        AVBProperty('value_type',     'OMFI:PRCL:ValueType',     'int16'),
        AVBProperty('extrap_kind',    'OMFI:PCRL:ExtrapKind',    'int32'),
        AVBProperty('control_points', 'OMFI:PRCL:ControlPoints', 'list'),
        AVBProperty('fields',         'OMFI:PRCL:Fields',        'int32'),
    ]

    def read(self, f):
        super(ParamClip, self).read(f)

        tag = read_byte(f)
        version = read_byte(f)

        assert tag == 0x02
        assert version == 0x01

        self.interp_kind = read_s32le(f)
        self.value_type = read_s16le(f)

        assert self.value_type in (CP_TYPE_INT, CP_TYPE_DOUBLE)

        point_count = read_s32le(f)
        assert point_count >= 0

        self.control_points = []
        for i in range(point_count):
            cp = ControlPoint(self.root)

            num = read_s32le(f)
            den = read_s32le(f)
            cp.offset = [num, den]
            cp.timescale = read_s32le(f)

            if self.value_type == CP_TYPE_INT:
                cp.value = read_s32le(f)
            elif self.value_type == CP_TYPE_DOUBLE:
                cp.value = read_doublele(f)
            else:
                raise ValueError("unknown value type: %d" % cp.type)

            pp_count = read_s16le(f)
            assert pp_count >= 0

            for j in range(pp_count):
                pp = PerPoint(self.root)
                pp.code = read_s16le(f)
                pp.type = read_s16le(f)

                if pp.type == CP_TYPE_DOUBLE:
                    pp.value = read_doublele(f)
                elif pp.type == CP_TYPE_INT:
                    pp.value  = read_s32le(f)
                else:
                    raise ValueError("unknown PP type: %d" % pp.type)

                cp.pp.append(pp)

            self.control_points.append(cp)

        for tag in iter_ext(f):
            if tag == 0x01:
                read_assert_tag(f, 71)
                self.extrap_kind = read_s32le(f)
            elif tag == 0x02:
                read_assert_tag(f, 71)
                self.fields = read_s32le(f)
            else:
                raise ValueError("%s: unknown ext tag 0x%02X %d" % (str(self.class_id), tag,tag))

        read_assert_tag(f, 0x03)

@utils.register_class
class Filler(Clip):
    class_id = b'FILL'

    def read(self, f):
        super(Filler, self).read(f)
        tag = read_byte(f)
        version = read_byte(f)
        end_tag = read_byte(f)

        assert tag == 0x02
        assert version == 0x01
        assert end_tag == 0x03
