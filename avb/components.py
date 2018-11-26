from __future__ import (
    unicode_literals,
    absolute_import,
    print_function,
    division,
    )

from . import core
from .core import AVBProperty
from . import utils

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

from . import mobid

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

class Track(core.AVBObject):
    properties = [
        AVBProperty('flags',            'OMFI:TRAK:OptFlags',       'int16'),
        AVBProperty('index',            'OMFI:TRAK:LabelNumber',    'int16'),
        AVBProperty('session_attr',     'OMFI:TRAK:SessionAttrs',   'reference'),
        AVBProperty('component',        'OMFI:TRAK:TrackComponent', 'reference'),
        AVBProperty('filler_proxy',     'OMFI:TRAK:FillerProxy',    'reference'),
        AVBProperty('bob_data',         '__OMFI:TRAK:Bob',          'reference'),
        AVBProperty('control_code',     'OMFI:TRAK:ControlCode',    'int16'),
        AVBProperty('control_sub_code', 'OMFI:TRAK:ControlSubCode', 'int16'),
        AVBProperty('lock_number',      'OMFI:TRAK:LockNubmer',     'int16'),

    ]
    def __init__(self, root):
        super(Track, self).__init__(root)
        self.refs = []

    @property
    def segment(self):
        for item in self.refs:
            obj = item.value
            if isinstance(obj, Component):
                return obj

@utils.register_class
class TrackGroup(Component):
    class_id = b'TRKG'
    properties = Component.properties + [
        AVBProperty('mc_mode',     'OMFI:TRKG:MC:Mode',     'int8'),
        AVBProperty('length',      'OMFI:TRKG:GroupLength',  'int32'),
        AVBProperty('num_scalars', 'OMFI:TRKG:NumScalars',  'int32'),
        AVBProperty('tracks',      'OMFI:TRKG:Tracks',      'list')
    ]

    def read(self, f):
        super(TrackGroup, self).read(f)

        tag = read_byte(f)
        version = read_byte(f)

        assert tag == 0x02
        assert version == 0x08

        self.mc_mode = read_byte(f)
        self.length = read_s32le(f)
        self.num_scalars = read_s32le(f)

        track_count = read_s32le(f)
        self.tracks = []

        # really annoying, tracks can have variable lengths!!
        has_tracks = True
        for i in range(track_count):
            # print(peek_data(f).encode("hex"))
            track = Track(self.root)
            track.flags = read_u16le(f)

            # PVOL has a different track structure
            # contains ref to CTRL and might have 1 or 2 control vars
            if track.flags in (36, 100,):
                ref = read_object_ref(self.root, f)
                track.refs.append(ref)
                track.index = i + 1
                track.control_code = read_s16le(f)
                if track.flags in (100, ):
                    track.control_sub_code = read_s16le(f)
                self.tracks.append(track)
                continue

            track.index = i + 1

            # these flags don't have track label
            # slct_01.chunk
            if track.flags not in (4, 12):
                track.index = read_s16le(f)


            if track.flags == 0 and track.index == 0:
                has_tracks = False
                break

            # print "{0:016b}".format(track.flags)
            # print( str(self.class_id), "index: %04d" % track.index, "flags 0x%04X" % track.flags, track.flags)
            ref_count = 1

            if track.flags in (4, 5):
                ref_count = 1
            elif track.flags in (12, 13, 21, 517,):
                ref_count = 2
            elif track.flags in (29, 519, 525, 533,  ):
                ref_count = 3
            elif track.flags in (541, 527):
                ref_count = 4

            # TODO: find sample?
            elif track.flags in (543,):
                ref_count = 5
            else:
                raise ValueError("%s: unknown track flag %d" % (str(self.class_id), track.flags))

            for j in range(ref_count):
                ref = read_object_ref(self.root, f)
                track.refs.append(ref)

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
class TrackEffect(TrackGroup):
    class_id = b'TKFX'
    def read(self, f):
        super(TrackEffect, self).read(f)
        tag = read_byte(f)
        version = read_byte(f)

        assert tag == 0x02
        assert version == 0x06

        self.left_length = read_s32le(f)
        self.right_length = read_s32le(f)

        self.info_version = read_s16le(f)
        self.info_current = read_s32le(f)
        self.info_smooth = read_s32le(f)
        self.info_color_item = read_s16le(f)
        self.info_quality = read_s16le(f)
        self.info_is_reversed = read_s8(f)
        self.info_aspect_on = read_bool(f)

        self.keyframes = read_object_ref(self.root, f)
        self.info_force_software = read_bool(f)
        self.info_never_hardware = read_bool(f)

        for tag in iter_ext(f):
            if tag == 0x02:
                read_assert_tag(f, 72)
                self.trackman = read_object_ref(self.root, f)
            else:
                raise ValueError("%s: unknown ext tag 0x%02X %d" % (str(self.class_id), tag,tag))

        if self.class_id is b'TKFX':
            tag = read_byte(f)
            assert tag == 0x03

@utils.register_class
class PanVolumeEffect(TrackEffect):
    class_id = b'PVOL'
    def read(self, f):
        super(PanVolumeEffect, self).read(f)

        tag = read_byte(f)
        version = read_byte(f)

        assert tag == 0x02
        assert version == 0x05

        self.level = read_s32le(f)
        self.pan = read_s32le(f)

        self.suppress_validation = read_bool(f)
        self.level_set = read_bool(f)
        self.pan_set = read_bool(f)

        for tag in iter_ext(f):
            if tag == 0x01:
                read_assert_tag(f, 71)
                self.does_support_seperate_clip_gain = read_s32le(f)
            elif tag == 0x02:
                read_assert_tag(f, 71)
                self.is_trim_gain_effect = read_s32le(f)
            else:
                raise ValueError("%s: unknown ext tag 0x%02X %d" % (str(self.class_id), tag,tag))

        tag = read_byte(f)
        assert tag == 0x03

class ASPIPlugin(object):
    def __init__(self):
        self.name = None
        self.manufacturer_id = None
        self.product_id = None
        self.plugin_id = None
        self.chunks = []

class ASPIPluginChunk(object):
    def __init__(self):
        self.version = None
        self.manufacturer_id = None
        self.product_id = None
        self.chunk_id = None
        self.name = None
        self.data = None

@utils.register_class
class ASPIPluginClip(TrackEffect):
    class_id = b'ASPI'
    def read(self, f):
        super(ASPIPluginClip, self).read(f)

        read_assert_tag(f, 0x02)
        read_assert_tag(f, 0x01)

        self.plugins = []

        number_of_plugins = read_s32le(f)

        #TODO: find sample with multiple plugins
        assert number_of_plugins == 1

        plugin = ASPIPlugin()
        plugin.name = read_string(f)
        plugin.manufacturer_id = read_u32le(f)
        plugin.product_id = read_u32le(f)
        plugin.plugin_id = read_u32le(f)

        num_of_chunks = read_s32le(f)

        #TODO: find sample with multiple chunks
        assert num_of_chunks == 1

        chunk_size = read_s32le(f)
        assert chunk_size >= 0

        chunk = ASPIPluginChunk()
        chunk.version = read_s32le(f)
        chunk.manufacturer_id = read_u32le(f)
        chunk.roduct_id = read_u32le(f)
        chunk.plugin_id = read_u32le(f)

        chunk.chunk_id = read_u32le(f)
        chunk.name = read_string(f)

        chunk.data = bytearray(f.read(chunk_size))

        plugin.chunks.append(chunk)
        self.plugins.append(plugin)

        # print(peek_data(f).encode("hex"))
        #
        # mob_id = mobid.MobID()
        # for tag in iter_ext(f):
        #     if tag == 0x01:
        #         read_assert_tag(f, 71)
        #         mob_id.instanceHigh = read_s32le(f)
        #         read_assert_tag(f, 71)
        #         mob_id.instanceLow = read_s32le(f)
        #     elif tag == 0x08:
        #         read_assert_tag(f, 65)
        #         mob_id.SMPTELabel = [read_byte(f) for i in range(12)]
        #
        #     else:
        #         raise ValueError("%s: unknown ext tag 0x%02X %d" % (str(self.class_id), tag,tag))
        #
        # raise Exception()

class EqualizerBand(object):
    def __init__(self):
        self.type = None
        self.freq = None
        self.gain = None
        self.q = None
        self.enable = None

@utils.register_class
class EqualizerMultiBand(TrackEffect):
    class_id = b'EQMB'

    def read(self, f):
        super(EqualizerMultiBand, self).read(f)
        # print(peek_data(f).encode("hex"))

        read_assert_tag(f, 0x02)
        read_assert_tag(f, 0x05)

        num_bands = read_s32le(f)
        assert num_bands >= 0

        self.bands = []
        for i in range(num_bands):
            band = EqualizerBand()
            band.type = read_s32le(f)
            band.freq = read_s32le(f)
            band.gain = read_s32le(f)
            band.q = read_s32le(f)
            band.enable = read_bool(f)
            self.bands.append(band)

        self.effect_enable = read_bool(f)
        self.filter_name = read_string(f)

        read_assert_tag(f, 0x03)

@utils.register_class
class RepSet(TrackGroup):
    class_id = b'RSET'
    def read(self, f):
        super(RepSet, self).read(f)

        # print(peek_data(f).encode("hex"))
        tag = read_byte(f)
        version = read_byte(f)

        assert tag == 0x02
        assert version == 0x01

        for tag in iter_ext(f):
            if tag == 0x01:
                read_assert_tag(f, 71)
                self.rep_set_type = read_s32le(f)
            else:
                raise ValueError("%s: unknown ext tag 0x%02X %d" % (str(self.class_id), tag,tag))

        tag = read_byte(f)
        assert tag == 0x03

#abstract?
class TimeWarp(TrackGroup):
    class_id = b'WARP'

    def read(self, f):
        super(TimeWarp, self).read(f)

        tag = read_byte(f)
        version = read_byte(f)

        assert tag == 0x02
        assert version == 0x02
        self.phase_offset = read_s32le(f)

@utils.register_class
class CaptureMask(TimeWarp):
    class_id = b'MASK'
    def read(self, f):
        super(CaptureMask, self).read(f)
        # print(peek_data(f).encode("hex"))

        tag = read_byte(f)
        version = read_byte(f)

        assert tag == 0x02
        assert version == 0x01

        self.is_double = read_bool(f)
        self.mask_bits = read_u32le(f)

        tag = read_byte(f)
        assert tag == 0x03

@utils.register_class
class MotionEffect(TimeWarp):
    class_id = b'SPED'
    def read(self, f):
        super(MotionEffect, self).read(f)
        # print(peek_data(f).encode("hex"))

        tag = read_byte(f)
        version = read_byte(f)

        assert tag == 0x02
        assert version == 0x03

        num = read_s32le(f)
        den = read_s32le(f)
        self.rate = [num, den]

        for tag in iter_ext(f):

            if tag == 0x01:
                read_assert_tag(f, 75)
                self.offset_adjust = read_doublele(f)
            elif tag == 0x02:
                read_assert_tag(f, 72)
                self.source_param_list = read_object_ref(self.root, f)
            elif tag == 0x03:
                read_assert_tag(f, 66)
                self.new_source_calculation = read_bool(f)
            else:
                raise ValueError("%s: unknown ext tag 0x%02X %d" % (str(self.class_id), tag,tag))

        tag = read_byte(f)
        assert tag == 0x03

@utils.register_class
class Repeat(TimeWarp):
    class_id = b'REPT'
    def read(self, f):
        super(Repeat, self).read(f)
        tag = read_byte(f)
        version = read_byte(f)
        assert tag == 0x02
        assert version == 0x01

        tag = read_byte(f)
        assert tag == 0x03


@utils.register_class
class TransistionEffect(TrackGroup):
    class_id = b'TNFX'
    def read(self, f):
        super(TransistionEffect, self).read(f)

        tag = read_byte(f)
        version = read_byte(f)

        assert tag == 0x02
        assert version == 0x01

        self.cutpoint = read_s32le(f)

        # the rest is the same as TKFX
        tag = read_byte(f)
        version = read_byte(f)
        assert tag == 0x02
        assert version == 0x05

        self.left_length = read_s32le(f)
        self.right_length = read_s32le(f)

        self.info_version = read_s16le(f)
        self.info_current = read_s32le(f)
        self.info_smooth = read_s32le(f)
        self.info_color_item = read_s16le(f)
        self.info_quality = read_s16le(f)
        self.info_is_reversed = read_s8(f)
        self.info_aspect_on = read_bool(f)

        self.keyframes = read_object_ref(self.root, f)
        self.info_force_software = read_bool(f)
        self.info_never_hardware = read_bool(f)

        for tag in iter_ext(f):
            if tag == 0x01:
                read_assert_tag(f, 72)
                self.trackman = read_object_ref(self.root, f)
            else:
                raise ValueError("%s: unknown ext tag 0x%02X %d" % (str(self.class_id), tag,tag))

        tag = read_byte(f)
        assert tag == 0x03

@utils.register_class
class Selector(TrackGroup):
    class_id = b'SLCT'

    def read(self, f):
        super(Selector, self).read(f)
        tag = read_byte(f)
        version = read_byte(f)

        assert tag == 0x02
        assert version == 0x01

        self.is_ganged = read_bool(f)
        self.selected = read_u16le(f)

        assert self.selected < len(self.tracks)

        tag = read_byte(f)
        assert tag == 0x03

    def components(self):
        for track in self.tracks:
            yield track.segment

@utils.register_class
class Composition(TrackGroup):
    class_id = b'CMPO'

    def read(self, f):
        super(Composition, self).read(f)
        tag = read_byte(f)
        version = read_byte(f)
        assert tag == 0x02
        assert version == 0x02

        mob_id_hi = read_s32le(f)
        mob_id_lo = read_s32le(f)
        self.last_modified = read_s32le(f)

        self.mob_type_id = read_byte(f)
        self.usage_code =  read_s32le(f)
        self.descriptor = read_object_ref(self.root, f)

        self.creation_time = None
        self.mob_id = None

        for tag in iter_ext(f):

            if tag == 0x01:
                read_assert_tag(f, 71)
                self.creation_time = read_datetime(f)
                self.mob_id = mobid.read_mob_id(f)
            else:
                raise ValueError("%s: unknown ext tag 0x%02X %d" % (str(self.class_id), tag,tag))

        read_assert_tag(f, 0x03)

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
