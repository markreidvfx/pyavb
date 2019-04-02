from __future__ import (
    unicode_literals,
    absolute_import,
    print_function,
    division,
    )

from . import core
from .core import AVBPropertyDef, AVBRefList
from . import utils
from . import mobid

from . utils import (
    read_u8, write_u8,
    read_s8,
    read_bool,
    read_s16le, write_s16le,
    read_u16le,
    read_u32le,
    read_s32le,
    read_string, write_string,
    read_doublele,
    read_exp10_encoded_float, write_exp10_encoded_float,
    read_object_ref, write_object_ref,
    read_datetime,
    iter_ext,
    read_assert_tag,
    peek_data
)



class Component(core.AVBObject):
    class_id = b'COMP'
    propertydefs = [
        AVBPropertyDef('left_bob',      '__OMFI:CPNT:LeftBob',    'reference'),
        AVBPropertyDef('right_bob',     '__OMFI:CPNT:RightBob',   'reference'),
        AVBPropertyDef('media_kind_id', 'OMFI:CPNT:TrackKind',    'int16'),
        AVBPropertyDef('edit_rate',     'EdRate',                 'fexp10'),
        AVBPropertyDef('name',          'OMFI:CPNT:Name',         'string'),
        AVBPropertyDef('effect_id',     'OMFI:CPNT:EffectID',     'string'),
        AVBPropertyDef('attributes',    'OMFI:CPNT:Attributes',   'reference'),
        AVBPropertyDef('session_attrs', 'OMFI:CPNT:SessionAttrs', 'reference'),
        AVBPropertyDef('precomputed',   'OMFI:CPNT:Precomputed',  'reference'),
        AVBPropertyDef('param_list',    'OMFI:CPNT:ParamList',    'reference'),
    ]
    __slots__ = ()

    def read(self, f):
        read_assert_tag(f, 0x02)
        read_assert_tag(f, 0x03)

        # bob == bytes of binary or bag of bits?
        self.left_bob =  read_object_ref(self.root, f)
        self.right_bob =  read_object_ref(self.root, f)

        self.media_kind_id = read_s16le(f)
        self.edit_rate = read_exp10_encoded_float(f)
        self.name = read_string(f) or None
        self.effect_id = read_string(f) or None

        self.attributes = read_object_ref(self.root, f)
        self.session_attrs = read_object_ref(self.root, f)

        self.precomputed = read_object_ref(self.root, f)

        for tag in iter_ext(f):

            if tag == 0x01:
                read_assert_tag(f, 72)
                self.param_list = read_object_ref(self.root, f)
            else:
                raise ValueError("%s: unknown ext tag 0x%02X %d" % (str(self.class_id), tag,tag))

    def write(self, f):
        write_u8(f, 0x02)
        write_u8(f, 0x03)
        write_object_ref(self.root, f, self.left_bob)
        write_object_ref(self.root, f, self.right_bob)
        write_s16le(f, self.media_kind_id)

        write_exp10_encoded_float(f, self.edit_rate)
        write_string(f, self.name)
        write_string(f, self.effect_id)

        write_object_ref(self.root, f, self.attributes)
        write_object_ref(self.root, f, self.session_attrs)
        write_object_ref(self.root, f, self.precomputed)

        if hasattr(self, 'param_list'):
            write_u8(f, 0x01)
            write_u8(f, 0x01)
            write_u8(f, 72)
            write_object_ref(self.root, f, self.param_list)

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
    propertydefs = Component.propertydefs + [
        AVBPropertyDef('components', 'OMFI:SEQU:Sequence', 'ref_list'),
    ]
    __slots__ = ()

    def read(self, f):
        super(Sequence, self).read(f)
        read_assert_tag(f, 0x02)
        read_assert_tag(f, 0x03)

        count = read_u32le(f)
        self.components = AVBRefList(self.root)
        for i in range(count):
            ref = read_object_ref(self.root, f)
            # print ref
            self.components.append(ref)

        tag = read_u8(f)
        assert tag == 0x03

    @property
    def length(self):
        l = 0
        for c in self.components:
            if c.class_id == b'TNFX':
                l -= c.length
            else:
                l += c.length
        return l

class Clip(Component):
    class_id = b'CLIP'
    propertydefs = Component.propertydefs + [
        AVBPropertyDef('length', 'OMFI:CLIP:Length', 'int32'),
    ]
    __slots__ = ()

    def read(self, f):
        super(Clip, self).read(f)
        read_assert_tag(f, 0x02)
        read_assert_tag(f, 0x01)
        self.length = read_u32le(f)

@utils.register_class
class SourceClip(Clip):
    class_id = b'SCLP'
    propertydefs = Clip.propertydefs + [
        AVBPropertyDef('track_id',   'OMFI:SCLP:SourceTrack',     'int16'),
        AVBPropertyDef('start_time', 'OMFI:SCLP:SourcePosition',  'int32'),
        AVBPropertyDef('mob_id',     'MobID',                     'MobID'),
    ]
    __slots__ = ()

    def read(self, f):
        super(SourceClip, self).read(f)
        read_assert_tag(f, 0x02)
        read_assert_tag(f, 0x03)

        mob_id_hi = read_s32le(f)
        mob_id_lo = read_s32le(f)

        self.track_id = read_s16le(f)
        self.start_time = read_s32le(f)
        self.mob_id = mobid.read_mob_id(f)

        # null mobid
        if mob_id_hi == 0 and mob_id_lo == 0:
            self.mob_id = mobid.MobID()

        read_assert_tag(f, 0x03)

@utils.register_class
class Timecode(Clip):
    class_id = b'TCCP'
    propertydefs = Clip.propertydefs + [
        AVBPropertyDef('flags', 'OMFI:TCCP:Flags',   'int32'),
        AVBPropertyDef('fps',   'OMFI:TCCP:FPS',     'int32'),
        AVBPropertyDef('start', 'OMFI:TCCP:StartTC', 'int32'),
    ]
    __slots__ = ()

    def read(self, f):
        super(Timecode, self).read(f)
        read_assert_tag(f, 0x02)
        read_assert_tag(f, 0x01)

        # drop ??
        self.flags = read_u32le(f)
        self.fps = read_u16le(f)

        # unused
        f.read(6)

        self.start = read_u32le(f)
        read_assert_tag(f, 0x03)

@utils.register_class
class Edgecode(Clip):
    class_id = b'ECCP'
    propertydefs = Clip.propertydefs + [
        AVBPropertyDef('header',      'OMFI:ECCP:Header',      'bytes'),
        AVBPropertyDef('film_kind',   'OMFI:ECCP:FilmKind',   'uint8'),
        AVBPropertyDef('code_format', 'OMFI:ECCP:CodeFormat', 'uint8'),
        AVBPropertyDef('base_perf',   'OMFI:ECCP:BasePerf',   'uint16'),
        AVBPropertyDef('start_ec',    'OMFI:ECCP:StartEC',    'int32'),
    ]
    __slots__ = ()

    def read(self, f):
        super(Edgecode, self).read(f)
        read_assert_tag(f, 0x02)
        read_assert_tag(f, 0x01)

        self.header = bytearray(f.read(8))
        self.film_kind = read_u8(f)
        self.code_format =  read_u8(f)
        self.base_perf = read_u16le(f)
        unused_a  = read_u32le(f)
        self.start_ec = read_s32le(f)

        read_assert_tag(f, 0x03)

@utils.register_class
class TrackRef(Clip):
    class_id = b'TRKR'
    propertydefs = Clip.propertydefs + [
        AVBPropertyDef('relative_scope', 'OMFI:TRKR:RelativeScope', 'int16'),
        AVBPropertyDef('relative_track', 'OMFI:TRKR:RelativeTrack', 'int16'),
    ]
    __slots__ = ()

    def read(self, f):
        super(TrackRef, self).read(f)
        read_assert_tag(f, 0x02)
        read_assert_tag(f, 0x01)

        self.relative_scope = read_s16le(f)
        self.relative_track = read_s16le(f)

        read_assert_tag(f, 0x03)

CP_TYPE_INT = 1
CP_TYPE_DOUBLE = 2

class ParamControlPoint(core.AVBObject):
    propertydefs = [
        AVBPropertyDef('offset',    'OMFI:PRCL:Offset',     'rational'),
        AVBPropertyDef('timescale', 'OMFI:PRCL:TimeScale',  'int32'),
        AVBPropertyDef('value',     'OMFI:PRCL:Value',      'number'), # int or double
        AVBPropertyDef('pp',        'OMFI:PRCL:PP',         'list'),
    ]
    __slots__ = ()

    def __init__(self, root):
        super(ParamControlPoint, self).__init__(root)
        self.pp = []

# not sure hwat PP's stands for
class ParamPerPoint(core.AVBObject):
    propertydefs = [
        AVBPropertyDef('code',  'OMFI:PRCL:PPCode',  'int16'),
        AVBPropertyDef('type',  'OMFI:PRCL:PPType',  'int16'),
        AVBPropertyDef('value', 'OMFI:PRCL:PPValue', 'number'), # int or double
    ]
    __slots__ = ()

@utils.register_class
class ParamClip(Clip):
    class_id = b'PRCL'
    propertydefs = Clip.propertydefs + [
        AVBPropertyDef('interp_kind',    'OMFI:PRCL:InterpKind',    'int32'),
        AVBPropertyDef('value_type',     'OMFI:PRCL:ValueType',     'int16'),
        AVBPropertyDef('extrap_kind',    'OMFI:PCRL:ExtrapKind',    'int32'),
        AVBPropertyDef('control_points', 'OMFI:PRCL:ControlPoints', 'list'),
        AVBPropertyDef('fields',         'OMFI:PRCL:Fields',        'int32'),
    ]
    __slots__ = ()

    def read(self, f):
        super(ParamClip, self).read(f)
        read_assert_tag(f, 0x02)
        read_assert_tag(f, 0x01)

        self.interp_kind = read_s32le(f)
        self.value_type = read_s16le(f)
        # print(self.value_type)
        # not sure what 4 is BOB data?
        assert self.value_type in (CP_TYPE_INT, CP_TYPE_DOUBLE, 4)

        point_count = read_s32le(f)
        assert point_count >= 0

        self.control_points = []
        for i in range(point_count):
            cp = ParamControlPoint(self.root)

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
                pp = ParamPerPoint(self.root)
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


class ControlPoint(core.AVBObject):
    propertydefs = [
        AVBPropertyDef('offset',     'OMFI:CTRL:Offset',    'rational'),
        AVBPropertyDef('time_scale', 'OMFI:CTRL:TimeScale', 'int32'),
        AVBPropertyDef('value',      'OMFI:CTRL:Value',     'bool'),
        AVBPropertyDef('pp',         'OMFI:CTRL:PP',        'list'),
    ]
    __slots__ = ()

class PerPoint(core.AVBObject):
    propertydefs = [
        AVBPropertyDef('code',    'OMFI:CTRL:PPCode',  'int16'),
        AVBPropertyDef('value',   'OMFI:CTRL:PP',      'rational'),
    ]
    __slots__ = ()


@utils.register_class
class ControlClip(Clip):
    class_id = b'CTRL'
    propertydefs = Clip.propertydefs + [
        AVBPropertyDef('interp_kind',    'OMFI:CTRL:InterpKin',    'int32'),
        AVBPropertyDef('control_points', 'OMFI:CTRL:ControlPoints', 'list'),
    ]
    __slots__ = ()

    def read(self, f):
        super(ControlClip, self).read(f)
        read_assert_tag(f, 0x02)
        read_assert_tag(f, 0x03)

        self.interp_kind = read_s32le(f)
        count = read_s32le(f)
        self.control_points = []
        # print(self.interp_kind, count)
        #
        # print(peek_data(f).encode("hex"))
        for i in range(count):
            cp = ControlPoint(self.root)
            a = read_s32le(f)
            b = read_s32le(f)
            cp.offset = [a, b]
            cp.time_scale = read_s32le(f)

            # TODO: find sample with this False
            has_value = read_bool(f)
            assert has_value == True

            a = read_s32le(f)
            b = read_s32le(f)
            cp.value = [a, b]
            cp.pp = []

            pp_count = read_s16le(f)
            assert pp_count >= 0
            for j in range(pp_count):
                pp = PerPoint(self.root)
                pp.code = read_s16le(f)
                a = read_s32le(f)
                b = read_s32le(f)
                pp.value = [a,b]
                cp.pp.append(pp)

            self.control_points.append(cp)

        read_assert_tag(f, 0x03)
        # raise Exception()

@utils.register_class
class Filler(Clip):
    class_id = b'FILL'
    __slots__ = ()

    def read(self, f):
        super(Filler, self).read(f)
        read_assert_tag(f, 0x02)
        read_assert_tag(f, 0x01)

        read_assert_tag(f, 0x03)
