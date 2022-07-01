from __future__ import (
    unicode_literals,
    absolute_import,
    print_function,
    division,
    )
import datetime

from . import core
from .core import AVBPropertyDef, AVBRefList
from .components import Component
from . import utils
from . import mobid
from . utils import peek_data

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

@utils.register_helper_class
class Track(core.AVBObject):
    propertydefs_dict = {}
    propertydefs = [
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

    @property
    def media_kind(self):
        if hasattr(self, 'component'):
            return self.component.media_kind

    @property
    def flags(self):
        flags = 0
        if 'index' in self.property_data:
            flags |= TRACK_LABEL_FLAG

        if 'attributes' in self.property_data:
            flags |= TRACK_ATTRIBUTES_FLAG

        if 'session_attr' in self.property_data:
            flags |= TRACK_SESSION_ATTR_FLAG

        if 'component' in self.property_data:
            flags |= TRACK_COMPONENT_FLAG

        if 'filler_proxy' in self.property_data:
            flags |= TRACK_FILLER_PROXY_FLAG

        if 'bob_data' in self.property_data:
            flags |= TRACK_BOB_DATA_FLAG

        if 'control_code' in self.property_data:
            flags |= TRACK_CONTROL_CODE_FLAG

        if 'control_sub_code' in self.property_data:
            flags |= TRACK_CONTROL_SUB_CODE_FLAG

        if 'start_pos' in self.property_data:
            flags |= TRACK_START_POS_FLAG

        if 'read_only' in self.property_data:
            flags |= TRACK_READ_ONLY_FLAG

        return flags


@utils.register_class
class TrackGroup(Component):
    class_id = b'TRKG'
    propertydefs_dict = {}
    propertydefs = Component.propertydefs + [
        AVBPropertyDef('mc_mode',     'OMFI:TRKG:MC:Mode',     'int8',    0),
        AVBPropertyDef('length',      'OMFI:TRKG:GroupLength',  'int32',  0),
        AVBPropertyDef('num_scalars', 'OMFI:TRKG:NumScalars',  'int32',   0),
        AVBPropertyDef('tracks',      'OMFI:TRKG:Tracks',      'list',     )
    ]
    __slots__ = ()

    def __init__(self, edit_rate=25, media_kind=None):
        super(TrackGroup, self).__init__(edit_rate=edit_rate, media_kind=media_kind)
        self.tracks = []

    def read(self, f):
        super(TrackGroup, self).read(f)
        ctx = self.root.ictx
        ctx.read_assert_tag(f, 0x02)
        ctx.read_assert_tag(f, 0x08)

        self.mc_mode = ctx.read_u8(f)
        self.length = ctx.read_s32(f)
        self.num_scalars = ctx.read_s32(f)

        track_count = ctx.read_s32(f)
        self.tracks = []
        # print("tracks:", track_count)
        # really annoying, tracks can have variable lengths!!

        for i in range(track_count):
            # print(peek_data(f).encode("hex"))
            track = Track.__new__(Track, root=self.root)
            flags = ctx.read_u16(f)

            if flags & TRACK_LABEL_FLAG:
                track.index = ctx.read_s16(f)

            if flags & TRACK_ATTRIBUTES_FLAG:
                track.attributes = ctx.read_object_ref(self.root, f)

            if flags & TRACK_SESSION_ATTR_FLAG:
                track.session_attr = ctx.read_object_ref(self.root, f)

            if flags & TRACK_COMPONENT_FLAG:
                track.component = ctx.read_object_ref(self.root, f)

            if flags & TRACK_FILLER_PROXY_FLAG:
                track.filler_proxy = ctx.read_object_ref(self.root, f)

            if flags & TRACK_BOB_DATA_FLAG:
                track.bob_data = ctx.read_object_ref(self.root, f)

            if flags & TRACK_CONTROL_CODE_FLAG:
                track.control_code = ctx.read_s16(f)

            if flags & TRACK_CONTROL_SUB_CODE_FLAG:
                track.control_sub_code = ctx.read_s16(f)

            if flags & TRACK_START_POS_FLAG:
                track.start_pos = ctx.read_s32(f)

            if flags & TRACK_READ_ONLY_FLAG:
                track.read_only = ctx.read_bool(f)

            if flags & TRACK_UNKNOWN_FLAGS:
                raise ValueError("Unknown Track Flag: %d" % flags)

            assert track.flags == flags

            self.tracks.append(track)

        for tag in ctx.iter_ext(f):
            if tag == 0x01:
                for i in range(track_count):
                    ctx.read_assert_tag(f, 69)
                    self.tracks[i].lock_number = ctx.read_s16(f)
            else:
                raise ValueError("%s: unknown ext tag 0x%02X %d" % (str(self.class_id), tag,tag))

    def write(self, f):
        super(TrackGroup, self).write(f)
        ctx = self.root.octx
        ctx.write_u8(f, 0x02)
        ctx.write_u8(f, 0x08)

        ctx.write_u8(f, self.mc_mode)
        ctx.write_s32(f, self.length)
        ctx.write_s32(f, self.num_scalars)

        ctx.write_s32(f, len(self.tracks))

        for track in self.tracks:
            flags = track.flags
            if flags & TRACK_UNKNOWN_FLAGS:
                raise ValueError("Unknown Track Flag: %d" % flags)

            ctx.write_u16(f, flags)
            if flags & TRACK_LABEL_FLAG:
                ctx.write_s16(f, track.index)

            if flags & TRACK_ATTRIBUTES_FLAG:
                ctx.write_object_ref(self.root, f, track.attributes)

            if flags & TRACK_SESSION_ATTR_FLAG:
                ctx.write_object_ref(self.root, f, track.session_attr)

            if flags & TRACK_COMPONENT_FLAG:
                ctx.write_object_ref(self.root, f, track.component)

            if flags & TRACK_FILLER_PROXY_FLAG:
                ctx.write_object_ref(self.root, f, track.filler_proxy)

            if flags & TRACK_BOB_DATA_FLAG:
                ctx.write_object_ref(self.root, f, track.bob_data)

            if flags & TRACK_CONTROL_CODE_FLAG:
                ctx.write_s16(f, track.control_code)

            if flags & TRACK_CONTROL_SUB_CODE_FLAG:
                ctx.write_s16(f, track.control_sub_code)

            if flags & TRACK_START_POS_FLAG:
                ctx.write_s32(f, track.start_pos)

            if flags & TRACK_READ_ONLY_FLAG:
                ctx.write_bool(f, track.read_only)

        if self.tracks:
            ctx.write_u8(f, 0x01)
            ctx.write_u8(f, 0x01)

            for i in range(len(self.tracks)):
                ctx.write_u8(f, 69)
                if hasattr(self.tracks[i], 'lock_number'):
                    ctx.write_s16(f, self.tracks[i].lock_number)
                else:
                    ctx.write_s16(f, 0)


@utils.register_class
class TrackEffect(TrackGroup):
    class_id = b'TKFX'
    propertydefs_dict = {}
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
        ctx = self.root.ictx
        ctx.read_assert_tag(f, 0x02)
        ctx.read_assert_tag(f, 0x06)

        self.left_length = ctx.read_s32(f)
        self.right_length = ctx.read_s32(f)

        self.info_version = ctx.read_s16(f)
        self.info_current = ctx.read_s32(f)
        self.info_smooth = ctx.read_s32(f)
        self.info_color_item = ctx.read_s16(f)
        self.info_quality = ctx.read_s16(f)
        self.info_is_reversed = ctx.read_s8(f)
        self.info_aspect_on = ctx.read_bool(f)

        self.keyframes = ctx.read_object_ref(self.root, f)
        self.info_force_software = ctx.read_bool(f)
        self.info_never_hardware = ctx.read_bool(f)

        for tag in ctx.iter_ext(f):
            if tag == 0x02:
                ctx.read_assert_tag(f, 72)
                self.trackman = ctx.read_object_ref(self.root, f)
            else:
                raise ValueError("%s: unknown ext tag 0x%02X %d" % (str(self.class_id), tag,tag))

        if self.class_id[:] == b'TKFX':
            ctx.read_assert_tag(f, 0x03)

    def write(self, f):
        super(TrackEffect, self).write(f)
        ctx = self.root.octx
        ctx.write_u8(f, 0x02)
        ctx.write_u8(f, 0x06)

        ctx.write_s32(f, self.left_length)
        ctx.write_s32(f, self.right_length)

        ctx.write_s16(f, self.info_version)
        ctx.write_s32(f, self.info_current)
        ctx.write_s32(f, self.info_smooth)
        ctx.write_s16(f, self.info_color_item)
        ctx.write_s16(f, self.info_quality)
        ctx.write_s8(f, self.info_is_reversed)
        ctx.write_bool(f, self.info_aspect_on)

        ctx.write_object_ref(self.root, f, self.keyframes)
        ctx.write_bool(f, self.info_force_software)
        ctx.write_bool(f, self.info_never_hardware)

        if hasattr(self, 'trackman'):
            ctx.write_u8(f, 0x01)
            ctx.write_u8(f, 0x02)
            ctx.write_u8(f, 72)
            ctx.write_object_ref(self.root, f, self.trackman)

        if self.class_id[:] == b'TKFX':
            ctx.write_u8(f, 0x03)

@utils.register_class
class PanVolumeEffect(TrackEffect):
    class_id = b'PVOL'
    propertydefs_dict = {}
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
        ctx = self.root.ictx
        ctx.read_assert_tag(f, 0x02)
        ctx.read_assert_tag(f, 0x05)

        self.level = ctx.read_s32(f)
        self.pan = ctx.read_s32(f)

        self.suppress_validation = ctx.read_bool(f)
        self.level_set = ctx.read_bool(f)
        self.pan_set = ctx.read_bool(f)

        for tag in ctx.iter_ext(f):
            if tag == 0x01:
                ctx.read_assert_tag(f, 71)
                self.supports_seperate_gain = ctx.read_s32(f)
            elif tag == 0x02:
                ctx.read_assert_tag(f, 71)
                self.is_trim_gain_effect = ctx.read_s32(f)
            else:
                raise ValueError("%s: unknown ext tag 0x%02X %d" % (str(self.class_id), tag,tag))

        ctx.read_assert_tag(f, 0x03)

    def write(self, f):
        super(PanVolumeEffect, self).write(f)
        ctx = self.root.octx
        ctx.write_u8(f, 0x02)
        ctx.write_u8(f, 0x05)

        ctx.write_s32(f, self.level)
        ctx.write_s32(f, self.pan)

        ctx.write_bool(f, self.suppress_validation)
        ctx.write_bool(f, self.level_set)
        ctx.write_bool(f, self.pan_set)

        if hasattr(self, 'supports_seperate_gain'):
            ctx.write_u8(f, 0x01)
            ctx.write_u8(f, 0x01)
            ctx.write_u8(f, 71)
            ctx.write_s32(f, self.supports_seperate_gain)
        if hasattr(self, 'is_trim_gain_effect'):
            ctx.write_u8(f, 0x01)
            ctx.write_u8(f, 0x02)
            ctx.write_u8(f, 71)
            ctx.write_s32(f, self.is_trim_gain_effect)

        ctx.write_u8(f, 0x03)

@utils.register_helper_class
class ASPIPlugin(core.AVBObject):
    propertydefs_dict = {}
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

@utils.register_helper_class
class ASPIPluginChunk(core.AVBObject):
    propertydefs_dict = {}
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
    propertydefs_dict = {}
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
        ctx = self.root.ictx
        ctx.read_assert_tag(f, 0x02)
        ctx.read_assert_tag(f, 0x01)

        self.plugins = []

        number_of_plugins = ctx.read_s32(f)

        #TODO: find sample with multiple plugins
        assert number_of_plugins == 1

        plugin = ASPIPlugin.__new__(ASPIPlugin, root=self.root)
        plugin.name = ctx.read_string(f)
        plugin.manufacturer_id = ctx.read_u32(f)
        plugin.product_id = ctx.read_u32(f)
        plugin.plugin_id = ctx.read_u32(f)
        # print(peek_data(f).encode("hex"))
        num_of_chunks = ctx.read_s32(f)

        #TODO: find sample with multiple chunks
        # print('chunks', num_of_chunks)
        assert num_of_chunks >= 0
        plugin.chunks = []
        for i in range(num_of_chunks):

            chunk_size = ctx.read_s32(f)
            assert chunk_size >= 0

            chunk = ASPIPluginChunk.__new__(ASPIPluginChunk, root=self.root)
            chunk.version = ctx.read_s32(f)
            chunk.manufacturer_id = ctx.read_u32(f)
            chunk.product_id = ctx.read_u32(f)
            chunk.plugin_id = ctx.read_u32(f)

            chunk.chunk_id = ctx.read_u32(f)
            chunk.name = ctx.read_string(f)

            chunk.data = bytearray(f.read(chunk_size))

            plugin.chunks.append(chunk)

        self.plugins.append(plugin)

        # print(peek_data(f).encode("hex"))


        for tag in ctx.iter_ext(f):
            if tag == 0x01:
                # not sure what is used for. skiping
                ctx.read_assert_tag(f, 71)
                mob_hi = ctx.read_s32(f)
                ctx.read_assert_tag(f, 71)
                mob_lo = ctx.read_s32(f)
            elif tag == 0x02:
                ctx.read_assert_tag(f, 77)
                self.mark_in = ctx.read_s64(f)
            elif tag == 0x03:
                ctx.read_assert_tag(f, 77)
                self.mark_out = ctx.read_s64(f)
            elif tag == 0x04:
                ctx.read_assert_tag(f, 72)
                self.tracks_to_affect = ctx.read_s32(f)
            elif tag == 0x05:
                ctx.read_assert_tag(f, 71)
                self.rendering_mode = ctx.read_s32(f)
            elif tag == 0x06:
                ctx.read_assert_tag(f, 71)
                self.padding_secs = ctx.read_s32(f)
            elif tag == 0x08:
                self.mob_id = ctx.read_mob_id(f)

            elif tag == 0x09:
                ctx.read_assert_tag(f, 72)
                preset_path_length = ctx.read_u32(f)
                if preset_path_length > 0:
                    ctx.read_assert_tag(f, 65)
                    length = ctx.read_u32(f)
                    assert preset_path_length == length
                    self.preset_path = bytearray(f.read(length))
                else:
                    self.preset_path = bytearray()
            else:
                raise ValueError("%s: unknown ext tag 0x%02X %d" % (str(self.class_id), tag,tag))

        ctx.read_assert_tag(f, 0x03)

    def write(self, f):
        super(AudioSuitePluginEffect, self).write(f)
        ctx = self.root.octx
        ctx.write_u8(f, 0x02)
        ctx.write_u8(f, 0x01)

        ctx.write_s32(f, len(self.plugins))
        for plugin in self.plugins:
            ctx.write_string(f, plugin.name)
            ctx.write_u32(f, plugin.manufacturer_id)
            ctx.write_u32(f, plugin.product_id)
            ctx.write_u32(f, plugin.plugin_id)

            ctx.write_s32(f, len(plugin.chunks))

            for chunk in plugin.chunks:

                ctx.write_s32(f, len(chunk.data))

                ctx.write_s32(f, chunk.version)
                ctx.write_u32(f, chunk.manufacturer_id)
                ctx.write_u32(f, chunk.product_id)
                ctx.write_u32(f, chunk.plugin_id)

                ctx.write_u32(f, chunk.chunk_id)
                ctx.write_string(f, chunk.name)

                f.write(chunk.data)

        if hasattr(self, 'mob_id'):
            ctx.write_u8(f, 0x01)
            ctx.write_u8(f, 0x01)

            mob_lo = self.mob_id.material.time_low
            mob_hi = self.mob_id.material.time_mid + (self.mob_id.material.time_hi_version << 16)
            ctx.write_u8(f, 71)
            ctx.write_s32(f, mob_lo)
            ctx.write_u8(f, 71)
            ctx.write_s32(f, mob_hi)

        # NOTE: out of order to match seen files
        if hasattr(self, 'mob_id'):
            ctx.write_u8(f, 0x01)
            ctx.write_u8(f, 0x08)
            ctx.write_mob_id(f, self.mob_id)

        if hasattr(self, 'mark_in'):
            ctx.write_u8(f, 0x01)
            ctx.write_u8(f, 0x02)
            ctx.write_u8(f, 77)
            ctx.write_s64(f, self.mark_in)
        if hasattr(self, 'mark_out'):
            ctx.write_u8(f, 0x01)
            ctx.write_u8(f, 0x03)
            ctx.write_u8(f, 77)
            ctx.write_s64(f, self.mark_out)
        if hasattr(self, 'tracks_to_affect'):
            ctx.write_u8(f, 0x01)
            ctx.write_u8(f, 0x04)
            ctx.write_u8(f, 72)
            ctx.write_s32(f, self.tracks_to_affect)
        if hasattr(self, 'rendering_mode'):
            ctx.write_u8(f, 0x01)
            ctx.write_u8(f, 0x05)
            ctx.write_u8(f, 71)
            ctx.write_s32(f, self.rendering_mode)
        if hasattr(self, 'padding_secs'):
            ctx.write_u8(f, 0x01)
            ctx.write_u8(f, 0x06)
            ctx.write_u8(f, 71)
            ctx.write_s32(f, self.padding_secs)
        if hasattr(self, 'preset_path'):
            ctx.write_u8(f, 0x01)
            ctx.write_u8(f, 0x09)
            ctx.write_u8(f, 72)
            # yes its twice for some reason
            ctx.write_u32(f, len(self.preset_path))
            if len(self.preset_path) > 0:
                ctx.write_u8(f, 65)
                ctx.write_u32(f, len(self.preset_path))
                f.write(self.preset_path)

        ctx.write_u8(f, 0x03)

@utils.register_helper_class
class EqualizerBand(core.AVBObject):
    propertydefs_dict = {}
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
    propertydefs_dict = {}
    propertydefs = TrackEffect.propertydefs + [
        AVBPropertyDef('bands',         'OMFI:EQBD:AV:Bands',        'list'),
        AVBPropertyDef('effect_enable', 'OMFI:EQMB:AV:EffectEnable', 'bool'),
        AVBPropertyDef('filter_name',   'OMFI:EQMB:AV:FilterName',   'string'),
    ]
    __slots__ = ()

    def read(self, f):
        super(EqualizerMultiBand, self).read(f)
        ctx = self.root.ictx
        ctx.read_assert_tag(f, 0x02)
        ctx.read_assert_tag(f, 0x05)

        num_bands = ctx.read_s32(f)
        assert num_bands >= 0

        self.bands = []
        for i in range(num_bands):
            band = EqualizerBand.__new__(EqualizerBand, root=self.root)
            band.type = ctx.read_s32(f)
            band.freq = ctx.read_s32(f)
            band.gain = ctx.read_s32(f)
            band.q = ctx.read_s32(f)
            band.enable = ctx.read_bool(f)
            self.bands.append(band)

        self.effect_enable = ctx.read_bool(f)
        self.filter_name = ctx.read_string(f)

        ctx.read_assert_tag(f, 0x03)

    def write(self, f):
        super(EqualizerMultiBand, self).write(f)
        ctx = self.root.octx
        ctx.write_u8(f, 0x02)
        ctx.write_u8(f, 0x05)

        ctx.write_s32(f, len(self.bands))
        for band in self.bands:
            ctx.write_s32(f, band.type)
            ctx.write_s32(f, band.freq)
            ctx.write_s32(f, band.gain)
            ctx.write_s32(f, band.q)
            ctx.write_bool(f, band.enable)

        ctx.write_bool(f, self.effect_enable)
        ctx.write_string(f, self.filter_name)

        ctx.write_u8(f, 0x03)

class TimeWarp(TrackGroup):
    class_id = b'WARP'
    propertydefs_dict = {}
    propertydefs = TrackGroup.propertydefs + [
        AVBPropertyDef('phase_offset', 'OMFI:WARP:PhaseOffset', 'int32'),
    ]
    __slots__ = ()

    def read(self, f):
        super(TimeWarp, self).read(f)
        ctx = self.root.ictx
        ctx.read_assert_tag(f, 0x02)
        ctx.read_assert_tag(f, 0x02)
        self.phase_offset = ctx.read_s32(f)

    def write(self, f):
        super(TimeWarp, self).write(f)
        ctx = self.root.octx
        ctx.write_u8(f, 0x02)
        ctx.write_u8(f, 0x02)
        ctx.write_s32(f, self.phase_offset)

@utils.register_class
class CaptureMask(TimeWarp):
    class_id = b'MASK'
    propertydefs_dict = {}
    propertydefs = TimeWarp.propertydefs + [
        AVBPropertyDef('is_double', 'OMFI:MASK:IsDouble', 'bool'),
        AVBPropertyDef('mask_bits', 'OMFI:MASK:MaskBits', 'int32'),
    ]
    __slots__ = ()

    def read(self, f):
        super(CaptureMask, self).read(f)
        ctx = self.root.ictx
        ctx.read_assert_tag(f, 0x02)
        ctx.read_assert_tag(f, 0x01)

        self.is_double = ctx.read_bool(f)
        self.mask_bits = ctx.read_u32(f)

        ctx.read_assert_tag(f, 0x03)

    def write(self, f):
        super(CaptureMask, self).write(f)
        ctx = self.root.octx
        ctx.write_u8(f, 0x02)
        ctx.write_u8(f, 0x01)

        ctx.write_bool(f, self.is_double)
        ctx.write_u32(f, self.mask_bits)

        ctx.write_u8(f, 0x03)

@utils.register_class
class StrobeEffect(TimeWarp):
    class_id = b'STRB'
    propertydefs_dict = {}
    propertydefs = TimeWarp.propertydefs + [
        AVBPropertyDef('strobe_value',  'OMFI:STRB:MC:StrobeVal',  'int32'),
    ]
    __slots__ = ()

    def read(self, f):
        super(StrobeEffect, self).read(f)
        ctx = self.root.ictx
        ctx.read_assert_tag(f, 0x02)
        ctx.read_assert_tag(f, 0x01)
        self.strobe_value = ctx.read_s32(f)
        ctx.read_assert_tag(f, 0x03)

    def write(self, f):
        super(StrobeEffect, self).write(f)
        ctx = self.root.octx
        ctx.write_u8(f, 0x02)
        ctx.write_u8(f, 0x01)
        ctx.write_s32(f, self.strobe_value)
        ctx.write_u8(f, 0x03)

@utils.register_class
class MotionEffect(TimeWarp):
    class_id = b'SPED'
    propertydefs_dict = {}
    propertydefs = TimeWarp.propertydefs + [
        AVBPropertyDef('speed_ratio',            'OMFI:SPED:Rate',                 'rational'),
        AVBPropertyDef('offset_adjust',          'OMIF:SPED:OffsetAdjust',         'double'),
        AVBPropertyDef('source_param_list',      'OMFI:SPED:SourceParamList',      'reference'),
        AVBPropertyDef('new_source_calculation', 'OMIF:SPED:NewSourceCalculation', 'bool'),
    ]
    __slots__ = ()

    def read(self, f):
        super(MotionEffect, self).read(f)
        ctx = self.root.ictx
        ctx.read_assert_tag(f, 0x02)
        ctx.read_assert_tag(f, 0x03)

        num = ctx.read_s32(f)
        den = ctx.read_s32(f)
        self.speed_ratio = [num, den]

        for tag in ctx.iter_ext(f):

            if tag == 0x01:
                ctx.read_assert_tag(f, 75)
                self.offset_adjust = ctx.read_double(f)
            elif tag == 0x02:
                ctx.read_assert_tag(f, 72)
                self.source_param_list = ctx.read_object_ref(self.root, f)
            elif tag == 0x03:
                ctx.read_assert_tag(f, 66)
                self.new_source_calculation = ctx.read_bool(f)
            else:
                raise ValueError("%s: unknown ext tag 0x%02X %d" % (str(self.class_id), tag,tag))

        ctx.read_assert_tag(f, 0x03)

    def write(self, f):
        super(MotionEffect, self).write(f)
        ctx = self.root.octx
        ctx.write_u8(f, 0x02)
        ctx.write_u8(f, 0x03)

        ctx.write_s32(f, self.speed_ratio[0])
        ctx.write_s32(f, self.speed_ratio[1])

        if hasattr(self, 'offset_adjust'):
            ctx.write_u8(f, 0x01)
            ctx.write_u8(f, 0x01)
            ctx.write_u8(f, 75)
            ctx.write_double(f, self.offset_adjust)
        if hasattr(self, 'source_param_list'):
            ctx.write_u8(f, 0x01)
            ctx.write_u8(f, 0x02)
            ctx.write_u8(f, 72)
            ctx.write_object_ref(self.root, f, self.source_param_list)
        if hasattr(self, 'new_source_calculation'):
            ctx.write_u8(f, 0x01)
            ctx.write_u8(f, 0x03)
            ctx.write_u8(f, 66)
            ctx.write_bool(f, self.new_source_calculation)

        ctx.write_u8(f, 0x03)

@utils.register_class
class Repeat(TimeWarp):
    class_id = b'REPT'
    propertydefs_dict = {}
    __slots__ = ()

    def read(self, f):
        super(Repeat, self).read(f)
        ctx = self.root.ictx
        ctx.read_assert_tag(f, 0x02)
        ctx.read_assert_tag(f, 0x01)

        ctx.read_assert_tag(f, 0x03)

    def write(self, f):
        super(Repeat, self).write(f)
        ctx = self.root.octx
        ctx.write_u8(f, 0x02)
        ctx.write_u8(f, 0x01)

        ctx.write_u8(f, 0x03)

@utils.register_class
class EssenceGroup(TrackGroup):
    class_id = b'RSET'
    propertydefs_dict = {}
    propertydefs = TrackGroup.propertydefs + [
        AVBPropertyDef('rep_set_type', 'OMFI:RSET:repSetType', 'int32'),
    ]
    __slots__ = ()

    def read(self, f):
        super(EssenceGroup, self).read(f)
        ctx = self.root.ictx
        ctx.read_assert_tag(f, 0x02)
        ctx.read_assert_tag(f, 0x01)

        for tag in ctx.iter_ext(f):
            if tag == 0x01:
                ctx.read_assert_tag(f, 71)
                self.rep_set_type = ctx.read_s32(f)
            else:
                raise ValueError("%s: unknown ext tag 0x%02X %d" % (str(self.class_id), tag,tag))

        ctx.read_assert_tag(f, 0x03)

    def write(self, f):
        super(EssenceGroup, self).write(f)
        ctx = self.root.octx
        ctx.write_u8(f, 0x02)
        ctx.write_u8(f, 0x01)

        if hasattr(self, 'rep_set_type'):
            ctx.write_u8(f, 0x01)
            ctx.write_u8(f, 0x01)
            ctx.write_u8(f, 71)
            ctx.write_s32(f, self.rep_set_type)

        ctx.write_u8(f, 0x03)

@utils.register_class
class TransitionEffect(TrackGroup):
    class_id = b'TNFX'
    propertydefs_dict = {}
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
        ctx = self.root.ictx
        ctx.read_assert_tag(f, 0x02)
        ctx.read_assert_tag(f, 0x01)

        self.cutpoint = ctx.read_s32(f)

        # the rest is the same as TKFX
        ctx.read_assert_tag(f, 0x02)
        ctx.read_assert_tag(f, 0x05)

        self.left_length = ctx.read_s32(f)
        self.right_length = ctx.read_s32(f)

        self.info_version = ctx.read_s16(f)
        self.info_current = ctx.read_s32(f)
        self.info_smooth = ctx.read_s32(f)
        self.info_color_item = ctx.read_s16(f)
        self.info_quality = ctx.read_s16(f)
        self.info_is_reversed = ctx.read_s8(f)
        self.info_aspect_on = ctx.read_bool(f)

        self.keyframes = ctx.read_object_ref(self.root, f)
        self.info_force_software = ctx.read_bool(f)
        self.info_never_hardware = ctx.read_bool(f)

        for tag in ctx.iter_ext(f):
            if tag == 0x01:
                ctx.read_assert_tag(f, 72)
                self.trackman = ctx.read_object_ref(self.root, f)
            else:
                raise ValueError("%s: unknown ext tag 0x%02X %d" % (str(self.class_id), tag,tag))

        ctx.read_assert_tag(f, 0x03)

    def write(self, f):
        super(TransitionEffect, self).write(f)
        ctx = self.root.octx
        ctx.write_u8(f, 0x02)
        ctx.write_u8(f, 0x01)

        ctx.write_s32(f, self.cutpoint)

        # the rest is the same as TKFX
        ctx.write_u8(f, 0x02)
        ctx.write_u8(f, 0x05)

        ctx.write_s32(f, self.left_length)
        ctx.write_s32(f, self.right_length)

        ctx.write_s16(f, self.info_version)
        ctx.write_s32(f, self.info_current)
        ctx.write_s32(f, self.info_smooth)
        ctx.write_s16(f, self.info_color_item)
        ctx.write_s16(f, self.info_quality)
        ctx.write_s8(f, self.info_is_reversed)
        ctx.write_bool(f, self.info_aspect_on)

        ctx.write_object_ref(self.root, f, self.keyframes)
        ctx.write_bool(f, self.info_force_software)
        ctx.write_bool(f, self.info_never_hardware)

        if hasattr(self, 'trackman'):
            ctx.write_u8(f, 0x01)
            ctx.write_u8(f, 0x01)
            ctx.write_u8(f, 72)
            ctx.write_object_ref(self.root, f, self.trackman)

        ctx.write_u8(f, 0x03)

@utils.register_class
class Selector(TrackGroup):
    class_id = b'SLCT'
    propertydefs_dict = {}
    propertydefs = TrackGroup.propertydefs + [
        AVBPropertyDef('is_ganged', 'OMFI:SLCT:IsGanged',      'bool'),
        AVBPropertyDef('selected',  'OMFI:SLCT:SelectedTrack', 'int16'),
    ]
    __slots__ = ()

    def read(self, f):
        super(Selector, self).read(f)
        ctx = self.root.ictx
        ctx.read_assert_tag(f, 0x02)
        ctx.read_assert_tag(f, 0x01)

        self.is_ganged = ctx.read_bool(f)
        self.selected = ctx.read_u16(f)

        assert self.selected < len(self.tracks)

        ctx.read_assert_tag(f, 0x03)

    def write(self, f):
        super(Selector, self).write(f)
        ctx = self.root.octx
        ctx.write_u8(f, 0x02)
        ctx.write_u8(f, 0x01)

        ctx.write_bool(f, self.is_ganged)
        ctx.write_u16(f, self.selected)

        ctx.write_u8(f, 0x03)

    def components(self):
        for track in self.tracks:
            yield track.component

@utils.register_class
class Composition(TrackGroup):
    class_id = b'CMPO'
    propertydefs_dict = {}
    propertydefs = TrackGroup.propertydefs + [
        AVBPropertyDef('last_modified', 'OMFI:MOBJ:LastModified',  'int32',        0),
        AVBPropertyDef('mob_type_id',   '__OMFI:MOBJ:MobType',     'int8',         2),
        AVBPropertyDef('usage_code',    'OMFI:MOBJ:UsageCode',     'int8',         0),
        AVBPropertyDef('descriptor',    'OMFI:MOBJ:PhysicalMedia', 'reference', None),
        AVBPropertyDef('creation_time', 'OMFI:MOBJ:_CreationTime', 'int32'),
        AVBPropertyDef('mob_id',        'MobID',                   'MobID'),
    ]
    __slots__ = ()

    def __init__(self, name='Mob', mob_type="MasterMob"):
        super(Composition, self).__init__()

        self.name = mob_type
        if mob_type == "CompositionMob":
            self.mob_type_id = 1

        elif mob_type == "MasterMob":
            self.mob_type_id = 2

        elif mob_type == "SourceMob":
            self.mob_type_id = 3
        else:
            ValueError("Unknown mob type: %d" % mob_type)

        self.mob_id = mobid.MobID.new()
        now = datetime.datetime.now()
        self.last_modified = now
        self.creation_time = now

    def read(self, f):
        super(Composition, self).read(f)
        ctx = self.root.ictx
        ctx.read_assert_tag(f, 0x02)
        ctx.read_assert_tag(f, 0x02)

        mob_id_lo = ctx.read_u32(f)
        mob_id_hi = ctx.read_u32(f)
        self.last_modified = ctx.read_datetime(f)

        self.mob_type_id = ctx.read_u8(f)
        self.usage_code =  ctx.read_s32(f)
        self.descriptor = ctx.read_object_ref(self.root, f)

        for tag in ctx.iter_ext(f):

            if tag == 0x01:
                ctx.read_assert_tag(f, 71)
                self.creation_time = ctx.read_datetime(f)
            elif tag == 0x02:
                self.mob_id = ctx.read_mob_id(f)
            else:
                raise ValueError("%s: unknown ext tag 0x%02X %d" % (str(self.class_id), tag,tag))

        ctx.read_assert_tag(f, 0x03)

    def write(self, f):
        super(Composition, self).write(f)
        ctx = self.root.octx
        ctx.write_u8(f, 0x02)
        ctx.write_u8(f, 0x02)

        lo = self.mob_id.material.time_low
        hi = self.mob_id.material.time_mid + (self.mob_id.material.time_hi_version << 16)
        ctx.write_u32(f, lo)
        ctx.write_u32(f, hi)
        ctx.write_datetime(f, self.last_modified)

        ctx.write_u8(f, self.mob_type_id)
        ctx.write_s32(f, self.usage_code)
        ctx.write_object_ref(self.root, f, self.descriptor)

        if hasattr(self, 'creation_time'):
            ctx.write_u8(f, 0x01)
            ctx.write_u8(f, 0x01)
            ctx.write_u8(f, 71)
            ctx.write_datetime(f, self.creation_time)

        if hasattr(self, 'mob_id'):
            ctx.write_u8(f, 0x01)
            ctx.write_u8(f, 0x02)
            ctx.write_mob_id(f, self.mob_id)

        ctx.write_u8(f, 0x03)

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
