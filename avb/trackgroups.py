from __future__ import (
    unicode_literals,
    absolute_import,
    print_function,
    division,
    )

from . import core
from .core import AVBPropertyDef, AVBRefList
from .components import Component
from . import utils
from . import mobid

from . utils import (
    read_u8, write_u8,
    read_s8,
    read_bool,  write_bool,
    read_s16le, write_s16le,
    read_u16le, write_u16le,
    read_u32le, write_u32le,
    read_s32le, write_s32le,
    read_s64le,
    read_string,
    read_doublele,
    read_exp10_encoded_float,
    read_object_ref, write_object_ref,
    read_datetime, write_datetime,
    iter_ext,
    read_assert_tag,
    peek_data
)

TRACK_LABEL_FLAG            = 1 << 0
TRACK_ATTRIBUTES_FLAG       = 1 << 1
TRACK_COMPONENT_FLAG        = 1 << 2
TRACK_FILLER_PROXY_FLAG     = 1 << 3
TRACK_BOB_DATA_FLAG         = 1 << 4
TRACK_CONTROL_CODE_FLAG     = 1 << 5
TRACK_CONTROL_SUB_CODE_FLAG = 1 << 6
TRACK_START_POS_FLAG        = 1 << 7
TRACK_READ_ONLY_FLAG        = 1 << 8
TRACK_SESSION_ATTR_FLAG     = 1 << 9

TRACK_UNKNOWN_FLAGS         = 0xFC00

class Track(core.AVBObject):
    propertydefs = [
        AVBPropertyDef('flags',            'OMFI:TRAK:OptFlags',       'int16'),
        AVBPropertyDef('index',            'OMFI:TRAK:LabelNumber',    'int16'),
        AVBPropertyDef('attributes',       'OMFI:TRAK:Attributes',     'reference'),
        AVBPropertyDef('session_attr',     'OMFI:TRAK:SessionAttrs',   'reference'),
        AVBPropertyDef('component',        'OMFI:TRAK:TrackComponent', 'reference'),
        AVBPropertyDef('filler_proxy',     'OMFI:TRAK:FillerProxy',    'reference'),
        AVBPropertyDef('bob_data',         '__OMFI:TRAK:Bob',          'reference'),
        AVBPropertyDef('control_code',     'OMFI:TRAK:ControlCode',    'int16'),
        AVBPropertyDef('control_sub_code', 'OMFI:TRAK:ControlSubCode', 'int16'),
        AVBPropertyDef('start_pos',        'OMFI:TRAK:StartPos',       'int32'),
        AVBPropertyDef('read_only',        '__OMFI:TRAK:ReadOnly',     'bool'),
        AVBPropertyDef('lock_number',      'OMFI:TRAK:LockNubmer',     'int16'),
    ]
    __slots__ = ()

    def __init__(self, root):
        super(Track, self).__init__(root)

    @property
    def media_kind(self):
        if hasattr(self, 'component'):
            return self.component.media_kind

@utils.register_class
class TrackGroup(Component):
    class_id = b'TRKG'
    propertydefs = Component.propertydefs + [
        AVBPropertyDef('mc_mode',     'OMFI:TRKG:MC:Mode',     'int8'),
        AVBPropertyDef('length',      'OMFI:TRKG:GroupLength',  'int32'),
        AVBPropertyDef('num_scalars', 'OMFI:TRKG:NumScalars',  'int32'),
        AVBPropertyDef('tracks',      'OMFI:TRKG:Tracks',      'list')
    ]
    __slots__ = ()

    def read(self, f):
        super(TrackGroup, self).read(f)
        read_assert_tag(f, 0x02)
        read_assert_tag(f, 0x08)

        self.mc_mode = read_u8(f)
        self.length = read_s32le(f)
        self.num_scalars = read_s32le(f)

        track_count = read_s32le(f)
        self.tracks = []
        # print("tracks:", track_count)
        # really annoying, tracks can have variable lengths!!
        has_tracks = True
        for i in range(track_count):
            # print(peek_data(f).encode("hex"))
            track = Track(self.root)
            track.flags = read_u16le(f)

            if track.flags & TRACK_LABEL_FLAG:
                track.index = read_s16le(f)

            if track.flags & TRACK_ATTRIBUTES_FLAG:
                track.attributes = read_object_ref(self.root, f)

            if track.flags & TRACK_SESSION_ATTR_FLAG:
                track.session_attr = read_object_ref(self.root, f)

            if track.flags & TRACK_COMPONENT_FLAG:
                track.component = read_object_ref(self.root, f)

            if track.flags & TRACK_FILLER_PROXY_FLAG:
                track.filler_proxy = read_object_ref(self.root, f)

            if track.flags & TRACK_BOB_DATA_FLAG:
                track.bob_data = read_object_ref(self.root, f)

            if track.flags & TRACK_CONTROL_CODE_FLAG:
                track.control_code = read_s16le(f)

            if track.flags & TRACK_CONTROL_SUB_CODE_FLAG:
                track.control_sub_code = read_s16le(f)

            if track.flags & TRACK_START_POS_FLAG:
                track.start_pos = read_s32le(f)

            if track.flags & TRACK_READ_ONLY_FLAG:
                track.read_only = read_bool(f)

            if track.flags & TRACK_UNKNOWN_FLAGS:
                raise ValueError("Unknown Track Flag: %d" % track.flags)

            self.tracks.append(track)

        read_assert_tag(f, 0x01)
        read_assert_tag(f, 0x01)

        for i in range(track_count):
            read_assert_tag(f, 69)
            lock = read_s16le(f)
            if has_tracks:
                self.tracks[i].lock_number = lock

    def write(self, f):
        super(TrackGroup, self).write(f)
        write_u8(f, 0x02)
        write_u8(f, 0x08)

        write_u8(f, self.mc_mode)
        write_s32le(f, self.length)
        write_s32le(f, self.num_scalars)

        write_s32le(f, len(self.tracks))

        # TODO: cacluate flags dynamically using hasattr
        for track in self.tracks:
            write_u16le(f, track.flags)
            if track.flags & TRACK_LABEL_FLAG:
                write_s16le(f, track.index)

            if track.flags & TRACK_ATTRIBUTES_FLAG:
                write_object_ref(self.root, f, track.attributes)

            if track.flags & TRACK_SESSION_ATTR_FLAG:
                write_object_ref(self.root, f, track.session_attr)

            if track.flags & TRACK_COMPONENT_FLAG:
                write_object_ref(self.root, f, track.component)

            if track.flags & TRACK_FILLER_PROXY_FLAG:
                write_object_ref(self.root, f, track.filler_proxy)

            if track.flags & TRACK_BOB_DATA_FLAG:
                write_object_ref(self.root, f, track.bob_data)

            if track.flags & TRACK_CONTROL_CODE_FLAG:
                write_s16le(f, track.control_code)

            if track.flags & TRACK_CONTROL_SUB_CODE_FLAG:
                write_s16le(f, track.control_sub_code)

            if track.flags & TRACK_START_POS_FLAG:
                write_s32le(f, track.start_pos)

            if track.flags & TRACK_READ_ONLY_FLAG:
                write_bool(f, track.read_only)

            if track.flags & TRACK_UNKNOWN_FLAGS:
                raise ValueError("Unknown Track Flag: %d" % track.flags)

        write_u8(f, 0x01)
        write_u8(f, 0x01)

        for i in range(len(self.tracks)):
            write_u8(f, 69)
            if hasattr(self.tracks[i], 'lock_number'):
                write_s16le(f, self.tracks[i].lock_number)
            else:
                write_s16le(f, 0)


@utils.register_class
class TrackEffect(TrackGroup):
    class_id = b'TKFX'
    propertydefs = TrackGroup.propertydefs + [
        AVBPropertyDef('left_length',         'OMFI:TKFX:MC:LeftLength',            'int32'),
        AVBPropertyDef('right_length',        'OMFI:TKFX:MC:RightLength',           'int32'),
        AVBPropertyDef('info_version',        'OMFI:TNFX:MC:GlobalInfoVersion',     'int16'),
        AVBPropertyDef('info_current',        'OMFI:TNFX:MC:GlobalInfo.kfCurrent',  'int32'),
        AVBPropertyDef('info_smooth',         'OMFI:TNFX:MC:GlobalInfo.kfSmooth',   'int32'),
        AVBPropertyDef('info_color_item',     'OMFI:TNFX:MC:GlobalInfo.colorItem',  'int16'),
        AVBPropertyDef('info_quality',        'OMFI:TNFX:MC:GlobalInfo.quality',    'int16'),
        AVBPropertyDef('info_is_reversed',    'OMFI:TNFX:MC:GlobalInfo.isReversed', 'int8'),
        AVBPropertyDef('info_aspect_on',      'OMFI:TNFX:MC:GlobalInfo.aspectOn',   'bool'),
        AVBPropertyDef('keyframes',           'OMFI:TKFX:MC:KeyFrameList',     'reference'),
        AVBPropertyDef('info_force_software', 'OMFI:TNFX:MC:ForceSoftware',         'bool'),
        AVBPropertyDef('info_never_hardware', 'OMFI:TKFX:MC:NeverHardware',         'bool'),
        AVBPropertyDef('trackman',            'OMFI:TKFX:MC:TrackMan',         'reference'),
    ]
    __slots__ = ()

    def read(self, f):
        super(TrackEffect, self).read(f)
        read_assert_tag(f, 0x02)
        read_assert_tag(f, 0x06)

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
            read_assert_tag(f, 0x03)

@utils.register_class
class PanVolumeEffect(TrackEffect):
    class_id = b'PVOL'
    propertydefs = TrackEffect.propertydefs + [
        AVBPropertyDef('level',                  'OMFI:PVOL:MC:Level',               'int32'),
        AVBPropertyDef('pan',                    'OMFI:PVOL:MC:Pan',                 'int32'),
        AVBPropertyDef('suppress_validation',    'OMFI:PVOL:MC:SuppressValidation',  'bool'),
        AVBPropertyDef('level_set',              'OMFI:PVOL:MC:LevelSet',            'bool'),
        AVBPropertyDef('pan_set',                'OMFI:PVOL:MC:PanSet',              'bool'),
        AVBPropertyDef('supports_seperate_gain', 'OMFI:PVOL:MC:DoesSuprtSeprtClipG', 'int32'),
        AVBPropertyDef('is_trim_gain_effect',    'OMFI:PVOL:MC:IsTrimGainEffect',    'int32'),
    ]
    __slots__ = ()

    def read(self, f):
        super(PanVolumeEffect, self).read(f)
        read_assert_tag(f, 0x02)
        read_assert_tag(f, 0x05)

        self.level = read_s32le(f)
        self.pan = read_s32le(f)

        self.suppress_validation = read_bool(f)
        self.level_set = read_bool(f)
        self.pan_set = read_bool(f)

        for tag in iter_ext(f):
            if tag == 0x01:
                read_assert_tag(f, 71)
                self.supports_seperate_gain = read_s32le(f)
            elif tag == 0x02:
                read_assert_tag(f, 71)
                self.is_trim_gain_effect = read_s32le(f)
            else:
                raise ValueError("%s: unknown ext tag 0x%02X %d" % (str(self.class_id), tag,tag))

        read_assert_tag(f, 0x03)

class ASPIPlugin(core.AVBObject):
    propertydefs = [
        AVBPropertyDef('name',             'OMFI:ASPI:plugInName',             'string'),
        AVBPropertyDef('manufacturer_id',  'OMFI:ASPI:plugInfManufacturerID',  'uint32'),
        AVBPropertyDef('product_id',       'OMFI:ASPI:plugInfProductID',       'uint32'),
        AVBPropertyDef('plugin_id',        'OMFI:ASPI:plugInfPlugInID',        'uint32'),
        AVBPropertyDef('chunks',           'OMFI:ASPI:plugInChunks',           'list'),
    ]
    __slots__ = ()

    def __init__(self, root):
        super(ASPIPlugin, self).__init__(root)
        self.chunks = []

class ASPIPluginChunk(core.AVBObject):
    propertydefs = [
        AVBPropertyDef('version',         'OMFI:ASPI:chunkfVersion',         'int32'),
        AVBPropertyDef('manufacturer_id', 'OMFI:ASPI:plugInfManufacturerID', 'uint32'),
        AVBPropertyDef('product_id',      'OMFI:ASPI:plugInfProductID',      'uint32'),
        AVBPropertyDef('plugin_id',       'OMFI:ASPI:plugInfPlugInID',       'uint32'),
        AVBPropertyDef('chunk_id',        'OMFI:ASPI:chunkfChunkID',         'uint32'),
        AVBPropertyDef('name',            'OMFI:ASPI:chunkfChunkName',       'string'),
        AVBPropertyDef('data',            'OMFI:ASPI:chunkfData',            'bytes'),
    ]
    __slots__ = ()

@utils.register_class
class AudioSuitePluginEffect(TrackEffect):
    class_id = b'ASPI'
    propertydefs = TrackEffect.propertydefs + [
        AVBPropertyDef('plugins',          'OMFI:ASPI:plugIns',                         'list'),
        AVBPropertyDef('mob_id',           'MobID',                                     'MobID'),
        AVBPropertyDef('mark_in',          'OMFI:ASPI:markInForSourceMasterClip',       'uint64'),
        AVBPropertyDef('mark_out',         'OMFI:ASPI:markOutForSourceMasterClip',      'uint64'),
        AVBPropertyDef('tracks_to_affect', 'OMFI:ASPI:tracksToAffect',                  'uint32'),
        AVBPropertyDef('rendering_mode',   'OMFI:ASPI:renderingMode',                   'int32'),
        AVBPropertyDef('padding_secs',     'OMFI:ASPI:paddingSecs',                     'int32'),
        AVBPropertyDef('preset_path',      'OMFI:ASPI:presetPath',                      'bytes'),
    ]
    __slots__ = ()

    def read(self, f):
        super(AudioSuitePluginEffect, self).read(f)
        read_assert_tag(f, 0x02)
        read_assert_tag(f, 0x01)

        self.plugins = []

        number_of_plugins = read_s32le(f)

        #TODO: find sample with multiple plugins
        assert number_of_plugins == 1

        plugin = ASPIPlugin(self.root)
        plugin.name = read_string(f)
        plugin.manufacturer_id = read_u32le(f)
        plugin.product_id = read_u32le(f)
        plugin.plugin_id = read_u32le(f)
        # print(peek_data(f).encode("hex"))
        num_of_chunks = read_s32le(f)

        #TODO: find sample with multiple chunks
        # print('chunks', num_of_chunks)
        assert num_of_chunks >= 0
        for i in range(num_of_chunks):

            chunk_size = read_s32le(f)
            assert chunk_size >= 0

            chunk = ASPIPluginChunk(self.root)
            chunk.version = read_s32le(f)
            chunk.manufacturer_id = read_u32le(f)
            chunk.product_id = read_u32le(f)
            chunk.plugin_id = read_u32le(f)

            chunk.chunk_id = read_u32le(f)
            chunk.name = read_string(f)

            chunk.data = bytearray(f.read(chunk_size))

            plugin.chunks.append(chunk)

        self.plugins.append(plugin)

        # print(peek_data(f).encode("hex"))


        for tag in iter_ext(f):
            if tag == 0x01:
                # not sure what is used for. skiping
                read_assert_tag(f, 71)
                mob_hi = read_s32le(f)
                read_assert_tag(f, 71)
                mob_lo = read_s32le(f)
            elif tag == 0x02:
                read_assert_tag(f, 77)
                self.mark_in = read_s64le(f)
            elif tag == 0x03:
                read_assert_tag(f, 77)
                self.mark_out = read_s64le(f)
            elif tag == 0x04:
                read_assert_tag(f, 72)
                self.tracks_to_affect = read_s32le(f)
            elif tag == 0x05:
                read_assert_tag(f, 71)
                self.rendering_mode = read_s32le(f)
            elif tag == 0x06:
                read_assert_tag(f, 71)
                self.padding_secs = read_s32le(f)
            elif tag == 0x08:
                mob_id = mobid.MobID()
                read_assert_tag(f, 65)
                length = read_s32le(f)
                assert length == 12
                mob_id.SMPTELabel = [read_u8(f) for i in range(12)]
                read_assert_tag(f, 68)
                mob_id.length = read_u8(f)
                read_assert_tag(f, 68)
                mob_id.instanceHigh = read_u8(f)
                read_assert_tag(f, 68)
                mob_id.instanceMid = read_u8(f)
                read_assert_tag(f, 68)
                mob_id.instanceLow = read_u8(f)
                read_assert_tag(f, 72)
                mob_id.Data1 = read_u32le(f)
                read_assert_tag(f, 70)
                mob_id.Data2 = read_u16le(f)
                read_assert_tag(f, 70)
                mob_id.Data3 = read_u16le(f)
                read_assert_tag(f, 65)
                length = read_s32le(f)
                assert length == 8
                mob_id.Data4 = [read_u8(f) for i in range(8)]
                self.mob_id = mob_id

            elif tag == 0x09:
                read_assert_tag(f, 72)
                preset_path_length = read_u32le(f)
                read_assert_tag(f, 65)
                length = read_u32le(f)
                assert preset_path_length == length
                self.preset_path = bytearray(f.read(length))
            else:
                raise ValueError("%s: unknown ext tag 0x%02X %d" % (str(self.class_id), tag,tag))

        read_assert_tag(f, 0x03)

class EqualizerBand(core.AVBObject):
    propertydefs = [
        AVBPropertyDef('type',   'OMFI:EQBD:AV:BandType',   'int32'),
        AVBPropertyDef('freq',   'OMFI:EQBD:AV:BandFreq',   'int32'),
        AVBPropertyDef('gain',   'OMFI:EQBD:AV:BandGain',   'int32'),
        AVBPropertyDef('q',      'OMFI:EQBD:AV:BandQ',      'int32'),
        AVBPropertyDef('enable', 'OMFI:EQBD:AV:BandEnable', 'bool'),
    ]
    __slots__ = ()

@utils.register_class
class EqualizerMultiBand(TrackEffect):
    class_id = b'EQMB'
    propertydefs = TrackEffect.propertydefs + [
        AVBPropertyDef('bands',         'OMFI:EQBD:AV:Bands',        'list'),
        AVBPropertyDef('effect_enable', 'OMFI:EQMB:AV:EffectEnable', 'bool'),
        AVBPropertyDef('filter_name',   'OMFI:EQMB:AV:FilterName',   'string'),
    ]
    __slots__ = ()

    def read(self, f):
        super(EqualizerMultiBand, self).read(f)
        read_assert_tag(f, 0x02)
        read_assert_tag(f, 0x05)

        num_bands = read_s32le(f)
        assert num_bands >= 0

        self.bands = []
        for i in range(num_bands):
            band = EqualizerBand(self.root)
            band.type = read_s32le(f)
            band.freq = read_s32le(f)
            band.gain = read_s32le(f)
            band.q = read_s32le(f)
            band.enable = read_bool(f)
            self.bands.append(band)

        self.effect_enable = read_bool(f)
        self.filter_name = read_string(f)

        read_assert_tag(f, 0x03)

class TimeWarp(TrackGroup):
    class_id = b'WARP'
    propertydefs = TrackGroup.propertydefs + [
        AVBPropertyDef('phase_offset', 'OMFI:WARP:PhaseOffset', 'int32'),
    ]
    __slots__ = ()

    def read(self, f):
        super(TimeWarp, self).read(f)
        read_assert_tag(f, 0x02)
        read_assert_tag(f, 0x02)
        self.phase_offset = read_s32le(f)

@utils.register_class
class CaptureMask(TimeWarp):
    class_id = b'MASK'
    propertydefs = TimeWarp.propertydefs + [
        AVBPropertyDef('is_double', 'OMFI:MASK:IsDouble', 'bool'),
        AVBPropertyDef('mask_bits', 'OMFI:MASK:MaskBits', 'int32'),
    ]
    __slots__ = ()

    def read(self, f):
        super(CaptureMask, self).read(f)
        read_assert_tag(f, 0x02)
        read_assert_tag(f, 0x01)

        self.is_double = read_bool(f)
        self.mask_bits = read_u32le(f)

        read_assert_tag(f, 0x03)

@utils.register_class
class MotionEffect(TimeWarp):
    class_id = b'SPED'
    propertydefs = TimeWarp.propertydefs + [
        AVBPropertyDef('speed_ratio',            'OMFI:SPED:Rate',                 'rational'),
        AVBPropertyDef('offset_adjust',          'OMIF:SPED:OffsetAdjust',         'double'),
        AVBPropertyDef('source_param_list',      'OMFI:SPED:SourceParamList',      'reference'),
        AVBPropertyDef('new_source_calculation', 'OMIF:SPED:NewSourceCalculation', 'bool'),
    ]
    __slots__ = ()

    def read(self, f):
        super(MotionEffect, self).read(f)
        read_assert_tag(f, 0x02)
        read_assert_tag(f, 0x03)

        num = read_s32le(f)
        den = read_s32le(f)
        self.speed_ratio = [num, den]

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

        read_assert_tag(f, 0x03)

@utils.register_class
class Repeat(TimeWarp):
    class_id = b'REPT'
    __slots__ = ()

    def read(self, f):
        super(Repeat, self).read(f)
        read_assert_tag(f, 0x02)
        read_assert_tag(f, 0x01)

        read_assert_tag(f, 0x03)

@utils.register_class
class EssenceGroup(TrackGroup):
    class_id = b'RSET'
    propertydefs = TrackGroup.propertydefs + [
        AVBPropertyDef('rep_set_type', 'OMFI:RSET:repSetType', 'int32'),
    ]
    __slots__ = ()

    def read(self, f):
        super(EssenceGroup, self).read(f)
        read_assert_tag(f, 0x02)
        read_assert_tag(f, 0x01)

        for tag in iter_ext(f):
            if tag == 0x01:
                read_assert_tag(f, 71)
                self.rep_set_type = read_s32le(f)
            else:
                raise ValueError("%s: unknown ext tag 0x%02X %d" % (str(self.class_id), tag,tag))

        read_assert_tag(f, 0x03)

@utils.register_class
class TransitionEffect(TrackGroup):
    class_id = b'TNFX'
    propertydefs = TrackGroup.propertydefs + [
        AVBPropertyDef('cutpoint',            'OMFI:TRAN:CutPoint',                   'int32'),
        AVBPropertyDef('left_length',         'OMFI:TNFX:MC:LeftLength',              'int32'),
        AVBPropertyDef('right_length',        'OMFI:TNFX:MC:RightLength',             'int32'),
        AVBPropertyDef('info_version',        'OMFI:TNFX:MC:GlobalInfoVersion',       'int16'),
        AVBPropertyDef('info_current',        'OMFI:TNFX:MC:GlobalInfo.kfCurrent',    'int32'),
        AVBPropertyDef('info_smooth',         'OMFI:TNFX:MC:GlobalInfo.kfSmooth',     'int32'),
        AVBPropertyDef('info_color_item',     'OMFI:TNFX:MC:GlobalInfo.colorItem',    'int16'),
        AVBPropertyDef('info_quality',        'OMFI:TNFX:MC:GlobalInfo.quality',      'int16'),
        AVBPropertyDef('info_is_reversed',    'OMFI:TNFX:MC:GlobalInfo.isReversed',   'int8'),
        AVBPropertyDef('info_aspect_on',      'OMFI:TNTNFXFX:MC:GlobalInfo.aspectOn', 'bool'),
        AVBPropertyDef('keyframes',           'OMFI:TNFX:MC:KeyFrameList',       'reference'),
        AVBPropertyDef('info_force_software', 'OMFI:TNFX:MC:ForceSoftware',           'bool'),
        AVBPropertyDef('info_never_hardware', 'OMFI:TNFX:MC:NeverHardware',           'bool'),
        AVBPropertyDef('trackman',            'OMFI:TNFX:MC:TrackMan',           'reference'),
    ]
    __slots__ = ()

    def read(self, f):
        super(TransitionEffect, self).read(f)
        read_assert_tag(f, 0x02)
        read_assert_tag(f, 0x01)

        self.cutpoint = read_s32le(f)

        # the rest is the same as TKFX
        read_assert_tag(f, 0x02)
        read_assert_tag(f, 0x05)

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

        read_assert_tag(f, 0x03)

@utils.register_class
class Selector(TrackGroup):
    class_id = b'SLCT'
    propertydefs = TrackGroup.propertydefs + [
        AVBPropertyDef('is_ganged', 'OMFI:SLCT:IsGanged',      'bool'),
        AVBPropertyDef('selected',  'OMFI:SLCT:SelectedTrack', 'int16'),
    ]
    __slots__ = ()

    def read(self, f):
        super(Selector, self).read(f)
        read_assert_tag(f, 0x02)
        read_assert_tag(f, 0x01)

        self.is_ganged = read_bool(f)
        self.selected = read_u16le(f)

        assert self.selected < len(self.tracks)

        read_assert_tag(f, 0x03)

    def components(self):
        for track in self.tracks:
            yield track.component

@utils.register_class
class Composition(TrackGroup):
    class_id = b'CMPO'
    propertydefs = TrackGroup.propertydefs + [
        AVBPropertyDef('last_modified', 'OMFI:MOBJ:LastModified',  'int32'),
        AVBPropertyDef('mob_type_id',   '__OMFI:MOBJ:MobType',     'int8'),
        AVBPropertyDef('usage_code',    'OMFI:MOBJ:UsageCode',     'int8'),
        AVBPropertyDef('descriptor',    'OMFI:MOBJ:PhysicalMedia', 'reference'),
        AVBPropertyDef('creation_time', 'OMFI:MOBJ:_CreationTime', 'int32'),
        AVBPropertyDef('mob_id',        'MobID',                   'MobID'),
    ]
    __slots__ = ()

    def read(self, f):
        super(Composition, self).read(f)
        read_assert_tag(f, 0x02)
        read_assert_tag(f, 0x02)

        mob_id_hi = read_s32le(f)
        mob_id_lo = read_s32le(f)
        self.last_modified = read_s32le(f)

        self.mob_type_id = read_u8(f)
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

    def write(self, f):
        write_u8(f, 0x02)
        write_u8(f, 0x02)

        write_s32le(f, self.mob_id.material.time_low)
        hi = self.mob_id.material.time_mid + (self.mob_id.material.time_hi_version << 16)
        write_s32le(f, hi)
        write_s32le(f, self.last_modified)

        write_u8(f, self.mob_type_id)
        write_s32le(f, self.usage_code)
        write_object_ref(self.root, f, self.descriptor)

        write_u8(f, 0x01)
        write_u8(f, 0x01)
        write_u8(f, 71)

        write_datetime(f, self.creation_time)
        # mobid.write_mob_id(f, self.mob_id)

    @property
    def usage(self):
        # these usage codes seem to come from omf
        if self.usage_code == 0:
            return None
        # master mob to a precompute
        elif self.usage_code == 1:
            return "precompute"
        # mob is a subclip
        elif self.usage_code == 2:
            return "subclip"
        # mob is an effect holder
        elif self.usage_code == 3:
            return "effect"
        # comp of selectors
        elif self.usage_code == 4:
            return "group"
        # mob that back up groups
        elif self.usage_code == 5:
            return "groupoofter"
        # motion effect clip
        elif self.usage_code == 6:
            return "motion"
        # group phys mobs
        elif self.usage_code == 7:
            return "mastermob"
        # file mob with a precompute
        elif self.usage_code == 9:
            return "precompute_file"
        else:
            return "unknown"

        #TODO: find out what code  8,10 -> 14 are
        # 14 essencegroup?

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
