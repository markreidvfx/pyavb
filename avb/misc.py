from __future__ import (
    unicode_literals,
    absolute_import,
    print_function,
    division,
    )

from . import core
from . import utils
from .core import AVBPropertyDef, AVBRefList
from . import mobid

from . utils import (
    read_byte,
    read_s8,
    read_bool,
    read_s16le,
    read_u16le,
    read_u32le,
    read_s32le,
    read_u64le,
    read_string,
    read_doublele,
    read_exp10_encoded_float,
    read_object_ref,
    read_datetime,
    read_raw_uuid,
    iter_ext,
    read_assert_tag,
    peek_data
)

class FileLocator(core.AVBObject):
    class_id = b'FILE'
    propertydefs = [
        AVBPropertyDef('path',       'OMFI:FL:PathName',       'string'),
        AVBPropertyDef('path_posix', 'OMFI:FL:POSIXPathName',  'string'),
        AVBPropertyDef('path_utf8',  'OMFI:FL:PathNameUTF8',   'string')
    ]
    __slots__ = ()

    def read(self, f):
        super(FileLocator, self).read(f)

        tag = read_byte(f)
        version = read_byte(f)

        assert tag == 0x02
        assert version == 2

        path = read_string(f)
        if path:
            self.path = path

        for tag in iter_ext(f):
            if tag == 0x01:
                read_assert_tag(f, 76)
                path = read_string(f)
                if path:
                    self.path_posix = path

            elif tag == 0x02:
                read_assert_tag(f, 76)
                path = read_string(f, 'utf-8')
                if path:
                    self.path_utf8 = path
            else:
                raise ValueError("%s: unknown ext tag 0x%02X %d" % (str(self.class_id), tag,tag))

        tag = read_byte(f)
        assert tag == 0x03

@utils.register_class
class MacFileLocator(FileLocator):
    class_id = b'FILE'
    __slots__ = ()

@utils.register_class
class WinFileLocator(FileLocator):
    class_id = b'WINF'
    __slots__ = ()

@utils.register_class
class GraphicEffect(core.AVBObject):
    class_id = b'GRFX'
    propertydefs = [
        AVBPropertyDef('pict_data', 'OMFI:MC:GRFX:PictData', 'bytes'),
    ]
    __slots__ = ()

    def read(self, f):
        super(GraphicEffect, self).read(f)
        read_assert_tag(f, 0x02)
        read_assert_tag(f, 0x01)

        pict_size = read_s32le(f)
        assert pict_size >= 0

        self.pict_data = bytearray(f.read(pict_size))
        assert len(self.pict_data) == pict_size

        read_assert_tag(f, 0x03)

class EffectParam(core.AVBObject):
    propertydefs = [
        AVBPropertyDef('percent_time',     'OMFI:FXPS:percentTime',         'int32'),
        AVBPropertyDef('level',            'OMFI:FXPS:level',               'int32'),
        AVBPropertyDef('pos_x',            'OMFI:FXPS:posX',                'int32'),
        AVBPropertyDef('floor_x',          'OMFI:FXPS:xFloor',              'int32'),
        AVBPropertyDef('ceil_x',           'OMFI:FXPS:xCeiling',            'int32'),
        AVBPropertyDef('pos_y',            'OMFI:FXPS:posY',                'int32'),
        AVBPropertyDef('floor_y',          'OMFI:FXPS:yFloor',              'int32'),
        AVBPropertyDef('ceil_y',           'OMFI:FXPS:yCeiling',            'int32'),
        AVBPropertyDef('scale_x',          'OMFI:FXPS:xScale',              'int32'),
        AVBPropertyDef('scale_y',          'OMFI:FXPS:yScale',              'int32'),
        AVBPropertyDef('crop_left',        'OMFI:FXPS:cropLeft',            'int32'),
        AVBPropertyDef('crop_right',       'OMFI:FXPS:cropRight',           'int32'),
        AVBPropertyDef('crop_top',         'OMFI:FXPS:cropTop',             'int32'),
        AVBPropertyDef('crop_bottom',      'OMFI:FXPS:cropBottom',          'int32'),
        AVBPropertyDef('box',              'OMFI:FXPS:box',                 'list'),
        AVBPropertyDef('box_xscale',       'OMFI:FXPS:boxLvl2Xscale',       'bool'),
        AVBPropertyDef('box_yscale',       'OMFI:FXPS:boxLvl2Yscale',       'bool'),
        AVBPropertyDef('box_xpos',         'OMFI:FXPS:FXboxLvl2Xpos',       'bool'),
        AVBPropertyDef('box_ypos',         'OMFI:FXPS:omFXboxLvl2Ypos',     'bool'),
        AVBPropertyDef('border_width',     'OMFI:FXPS:borderWidth',         'int32'),
        AVBPropertyDef('border_soft',      'OMFI:FXPS:borderSoft',          'int32'),
        AVBPropertyDef('splill_gain2',     'OMFI:FXPS:spillSecondGain',     'int16'),
        AVBPropertyDef('splill_gain',      'OMFI:FXPS:spillGain',           'int16'),
        AVBPropertyDef('splill_soft2',     'OMFI:FXPS:spillSecondSoft',     'int16'),
        AVBPropertyDef('splill_soft',      'OMFI:FXPS:spillSoft',           'int16'),
        AVBPropertyDef('enable_key_flags', 'OMFI:FXPS:enableKeyFlags',      'int8'),
        AVBPropertyDef('colors',           'OMFI:FXPS:Colors',              'list'),
        AVBPropertyDef('user_param',       'OMFI:FXPS:userParam',           'bytes'),
        AVBPropertyDef('selected',         'OMFI:FXPS:selected',            'bool'),
    ]
    __slots__ = ()

@utils.register_class
class EffectParamList(core.AVBObject):
    class_id = b'FXPS'
    propertydefs = [
        AVBPropertyDef('orig_length',   'OMFI:FXPS:originalLength',   'int32'),
        AVBPropertyDef('window_offset', 'OMFI:FXPS:omFXwindowOffset', 'int32'),
        AVBPropertyDef('keyframe_size', 'OMFI:FXPS:keyFrameSize',     'int32'),
    ]
    __slots__ = ()

    def read(self, f):
        super(EffectParamList, self).read(f)
        read_assert_tag(f, 0x02)
        read_assert_tag(f, 0x12)

        self.orig_length = read_s32le(f)
        self.window_offset = read_s32le(f)

        count = read_s32le(f)
        self.keyframe_size = read_s32le(f)

        for i in range(count):
            p = EffectParam(self.root)
            start = f.tell()
            p.percent_time = read_s32le(f)
            p.level = read_s32le(f)
            p.pos_x = read_s32le(f)
            p.floor_x = read_s32le(f)
            p.ceil_x = read_s32le(f)
            p.pos_y = read_s32le(f)
            p.floor_y = read_s32le(f)
            p.ceil_y = read_s32le(f)
            p.scale_x = read_s32le(f)
            p.scale_y = read_s32le(f)

            p.crop_left = read_s32le(f)
            p.crop_right = read_s32le(f)
            p.crop_top = read_s32le(f)
            p.crop_bottom = read_s32le(f)

            p.box = []
            # boxTop
            p.box.append(read_s32le(f))
            # boxBottom
            p.box.append(read_s32le(f))
            # boxTop repeat??
            p.box.append(read_s32le(f))
            # boxRight
            p.box.append(read_s32le(f))

            p.box_xscale = read_bool(f)
            p.box_yscale = read_bool(f)
            p.box_xpos = read_bool(f)
            p.box_ypos = read_bool(f)

            p.border_width = read_s32le(f)
            p.border_soft = read_s32le(f)

            p.splill_gain2 = read_s16le(f)
            p.splill_gain = read_s16le(f)
            p.splill_soft2 = read_s16le(f)
            p.splill_soft = read_s16le(f)

            p.enable_key_flags = read_s8(f)

            p.colors = []
            color_count = read_s32le(f)
            assert color_count >= 0
            for j in range(color_count):
                color = read_s32le(f)
                p.colors.append(color)

            param_size = read_s32le(f)
            assert param_size >= 0

            p.user_param = bytearray(f.read(param_size))
            p.selected = read_bool(f)

        read_assert_tag(f, 0x03)

@utils.register_class
class CFUserParam(core.AVBObject):
    class_id = b'AVUP'
    propertydefs = [
        AVBPropertyDef('byte_order', 'OMFI:AVUP:ByteOrder', 'uint16'),
        AVBPropertyDef('uuid',       'OMFI:AVUP:TypeID',    'UUID'),
        AVBPropertyDef('data',       'OMFI:AVUP:ValueData', 'bytes'),
    ]
    __slots__ = ()

    def read(self, f):
        super(CFUserParam, self).read(f)
        read_assert_tag(f, 0x02)
        read_assert_tag(f, 0x01)

        self.byte_order = read_s16le(f)
        assert self.byte_order == 0x4949

        self.uuid = read_raw_uuid(f)

        value_size = read_s32le(f)
        value_size = read_s32le(f)

        self.data = bytearray(f.read(value_size))

        read_assert_tag(f, 0x03)

@utils.register_class
class ParameterItems(core.AVBObject):
    class_id = b'PRIT'
    propertydefs = [
        AVBPropertyDef('uuid',            'OMFI:PRIT:GUID',                   'UUID'),
        AVBPropertyDef('value_type',      'OMFI:PRIT:ValueType',              'int16'),
        AVBPropertyDef('value',           'OMFI:PRIT:Value',                  'int32'),
        AVBPropertyDef('name',            'OMFI:PRIT:Name',                   'string'),
        AVBPropertyDef('enable',          'OMFI:PRIT:Enabled',                'bool'),
        AVBPropertyDef('control_track',   'OMFI:PRIT:ControlTrack',           'reference'),
        AVBPropertyDef('contribs_to_sig', 'OMFI:PRIT:ContributesToSignature', 'bool'),
    ]
    __slots__ = ()

    def read(self, f):
        super(ParameterItems, self).read(f)
        # print(peek_data(f).encode('hex'))
        read_assert_tag(f, 0x02)
        read_assert_tag(f, 0x02)

        self.uuid = read_raw_uuid(f)
        self.value_type = read_s16le(f)
        if self.value_type == 1:
            self.value = read_s32le(f)
        elif self.value_type == 2:
            self.value = read_doublele(f)
        elif self.value_type == 4:
            self.value = read_object_ref(self.root, f)
        else:
            raise ValueError("unknown value_type: %d" % self.value_type)

        self.name = read_string(f)
        self.enable = read_bool(f)
        self.control_track = read_object_ref(self.root, f)

        for tag in iter_ext(f):
            if tag == 0x01:
                read_assert_tag(f, 66)
                self.contribs_to_sig = read_bool(f)
            else:
                raise ValueError("%s: unknown ext tag 0x%02X %d" % (str(self.class_id), tag,tag))

        read_assert_tag(f, 0x03)

@utils.register_class
class MSMLocator(core.AVBObject):
    class_id = b'MSML'
    propertydefs = [
        AVBPropertyDef('last_known_volume',        'OMFI:MSML:LastKnownVolume',      'string'),
        AVBPropertyDef('domain_type',              'OMFI:MSML:DomainType',           'int32'),
        AVBPropertyDef('mob_id',                   'MobID',                          'MobID'),
        AVBPropertyDef('last_known_volume_utf8',   'OMFI:MSML:LastKnownVolumeUTF8', 'string'),
    ]
    __slots__ = ()

    def read(self, f):
        super(MSMLocator, self).read(f)
        # print(peek_data(f).encode('hex'))
        read_assert_tag(f, 0x02)
        read_assert_tag(f, 0x02)

        mob_id_hi = read_s32le(f)
        mob_id_lo = read_s32le(f)

        self.last_known_volume = read_string(f)

        for tag in iter_ext(f):

            if tag == 0x01:
                read_assert_tag(f, 71)
                self.domain_type = read_s32le(f)
            elif tag == 0x02:
                mob_id = mobid.MobID()
                read_assert_tag(f, 65)
                length = read_s32le(f)
                assert length == 12
                mob_id.SMPTELabel = [read_byte(f) for i in range(12)]
                read_assert_tag(f, 68)
                mob_id.length = read_byte(f)
                read_assert_tag(f, 68)
                mob_id.instanceHigh = read_byte(f)
                read_assert_tag(f, 68)
                mob_id.instanceMid = read_byte(f)
                read_assert_tag(f, 68)
                mob_id.instanceLow = read_byte(f)
                read_assert_tag(f, 72)
                mob_id.Data1 = read_u32le(f)
                read_assert_tag(f, 70)
                mob_id.Data2 = read_u16le(f)
                read_assert_tag(f, 70)
                mob_id.Data3 = read_u16le(f)
                read_assert_tag(f, 65)
                length = read_s32le(f)
                assert length == 8
                mob_id.Data4 = [read_byte(f) for i in range(8)]
                self.mob_id = mob_id
            elif tag == 0x03:
                read_assert_tag(f, 76)
                self.last_known_volume_utf8 = read_string(f, 'utf-8')
            else:
                raise ValueError("%s: unknown ext tag 0x%02X %d" % (str(self.class_id), tag,tag))

        read_assert_tag(f, 0x03)

@utils.register_class
class Position(core.AVBObject):
    class_id = b'APOS'
    propertydefs = [
        AVBPropertyDef('mob_id', "MobID", 'MobID'),
    ]
    __slots__ = ()

    def read(self, f):
        super(Position, self).read(f)
        read_assert_tag(f, 0x02)
        read_assert_tag(f, 0x01)

        mob_id_hi = read_s32le(f)
        mob_id_lo = read_s32le(f)

        self.mob_id = mobid.read_mob_id(f)

        if self.class_id ==  b'APOS':
            read_assert_tag(f, 0x03)


@utils.register_class
class BOBPosition(Position):
    class_id = b'ABOB'
    propertydefs = Position.propertydefs + [
        AVBPropertyDef('sample_num',  "__OMFI:MSBO:sampleNum",   'int32'),
        AVBPropertyDef('length',      "__OMFI:MSBO:length",      'int32'),
        AVBPropertyDef('track_type',  "OMFI:trkt:Track.trkType", 'int32'),
        AVBPropertyDef('track_index', "OMFI:trkt:Track.trkLNum", 'int32'),
    ]
    __slots__ = ()

    def read(self, f):
        super(BOBPosition, self).read(f)

        read_assert_tag(f, 0x02)
        read_assert_tag(f, 0x01)

        self.sample_num = read_s32le(f)
        self.length = read_s32le(f)
        self.track_type = read_s16le(f)
        self.track_index = read_s16le(f)

        if self.class_id ==  b'ABOB':
            read_assert_tag(f, 0x03)

@utils.register_class
class DIDPosition(BOBPosition):
    class_id = b'DIDP'
    propertydefs = BOBPosition.propertydefs + [
        AVBPropertyDef('strip',        "_Strip",       'int32'),
        AVBPropertyDef('offset',       "_Offset",      'uint64'),
        AVBPropertyDef('byte_length',  "_ByteLength",  'uint64'),
        AVBPropertyDef('spos_invalid', "_SPosInvalid", 'bool'),
    ]
    __slots__ = ()

    def read(self, f):
        super(DIDPosition, self).read(f)

        read_assert_tag(f, 0x02)
        read_assert_tag(f, 0x01)

        self.strip = read_s32le(f)
        self.offset = read_u64le(f)
        self.byte_length = read_u64le(f)
        self.spos_invalid = read_bool(f)

        read_assert_tag(f, 0x03)

@utils.register_class
class BinRef(core.AVBObject):
    class_id = b'MCBR'
    propertydefs = [
        AVBPropertyDef('uid_high',  'OMFI:MCBR:MC:binID.high',  'int32'),
        AVBPropertyDef('uid_low',   'OMFI:MCBR:MC:binID.low',   'int32'),
        AVBPropertyDef('name',      'OMFI:MCBR:MC:binName',     'string'),
        AVBPropertyDef('name_utf8', 'OMFI:MCBR:MC:binNameUTF8', 'string'),
    ]
    __slots__ = ()

    def read(self, f):
        super(BinRef, self).read(f)

        read_assert_tag(f, 0x02)
        read_assert_tag(f, 0x01)

        self.uid_high = read_s32le(f)
        self.uid_low = read_s32le(f)
        self.name = read_string(f)

        for tag in iter_ext(f):
            if tag == 0x01:
                read_assert_tag(f, 76)
                self.name_utf8 = read_string(f,'utf-8')
            else:
                raise ValueError("%s: unknown ext tag 0x%02X %d" % (str(self.class_id), tag,tag))

        read_assert_tag(f, 0x03)

@utils.register_class
class MobRef(core.AVBObject):
    class_id = b'MCMR'
    propertydefs = [
            AVBPropertyDef('position',      'OMFI:MCMR:MC:Position', 'int32'),
            AVBPropertyDef('mob_id',        'MobID', 'MobID'),
    ]
    __slots__ = ()

    def read(self, f):
        super(MobRef, self).read(f)
        read_assert_tag(f, 0x02)
        read_assert_tag(f, 0x01)

        mob_hi = read_s32le(f)
        mob_lo = read_s32le(f)
        self.position = read_s32le(f)

        self.mob_id = mobid.read_mob_id(f)

        if self.class_id == b'MCMR':
            read_assert_tag(f, 0x03)

# also called a TimeCrumb
@utils.register_class
class Marker(MobRef):
    class_id = b'TMBC'
    propertydefs = MobRef.propertydefs + [
        AVBPropertyDef('comp_offset',   'OMFI:TMBC:MC:CompOffset',             'int32'),
        AVBPropertyDef('attributes',    'OMFI:TMBC:MC:Attributes',             'reference'),
        AVBPropertyDef('color',         'OMFI:TMBC:MC:CarbonAPI::RGBColor',    'list'),
        AVBPropertyDef('handled_codes', 'OMFI:TMBC:MC:handledBadControlCodes', 'bool'),
    ]
    __slots__ = ()

    def read(self, f):
        super(Marker, self).read(f)

        read_assert_tag(f, 0x02)
        read_assert_tag(f, 0x03)

        self.comp_offset = read_s32le(f)
        self.attributes = read_object_ref(self.root, f)
        # print(self.comp_offset, self.attributes)

        version = read_s16le(f)
        assert version == 1

        self.color = []
        self.color.append(read_u16le(f))
        self.color.append(read_u16le(f))
        self.color.append(read_u16le(f))

        for tag in iter_ext(f):

            if tag == 0x01:
                read_assert_tag(f, 66)
                self.handled_codes = read_bool(f)
            else:
                raise ValueError("%s: unknown ext tag 0x%02X %d" % (str(self.class_id), tag,tag))

        read_assert_tag(f, 0x03)

@utils.register_class
class TrackerManager(core.AVBObject):
    class_id = b'TKMN'
    propertydefs = [
        AVBPropertyDef('data_slots',  'OMFI:TKMN:TrackerDataSlots',  'reference'),
        AVBPropertyDef('param_slots', 'OMFI:TKMN:TrackedParamSlots', 'reference'),
    ]
    __slots__ = ()

    def read(self, f):
        super(TrackerManager, self).read(f)
        read_assert_tag(f, 0x02)
        read_assert_tag(f, 0x01)

        self.data_slots = read_object_ref(self.root, f)
        self.param_slots = read_object_ref(self.root, f)

        read_assert_tag(f, 0x03)

@utils.register_class
class TrackerDataSlot(core.AVBObject):
    class_id = b'TKDS'
    propertydefs = [
        AVBPropertyDef('tracker_data',  'OMFI:TKDS:TrackerData',      'ref_list'),
        AVBPropertyDef('track_fg',      'OMFI:TKDAS:TrackForeground', 'bool'),
    ]
    __slots__ = ()

    def read(self, f):
        super(TrackerDataSlot, self).read(f)
        read_assert_tag(f, 0x02)
        read_assert_tag(f, 0x01)

        count = read_s32le(f)
        self.tracker_data = AVBRefList(self.root)
        for i in range(count):
            ref = read_object_ref(self.root, f)
            self.tracker_data.append(ref)

        for tag in iter_ext(f):
            if tag == 0x01:
                read_assert_tag(f, 66)
                self.track_fg = read_bool(f)
            else:
                raise ValueError("%s: unknown ext tag 0x%02X %d" % (str(self.class_id), tag,tag))

        read_assert_tag(f, 0x03)

@utils.register_class
class TrackerParameterSlot(core.AVBObject):
    class_id = b'TKPS'
    propertydefs = [
        AVBPropertyDef('settings', 'OMFI:TKPS:EffectSettings', 'bytes'),
        AVBPropertyDef('params',   'OMFI:TKPS:TrackedParam',   'ref_list'),
    ]
    __slots__ = ()

    def read(self, f):
        super(TrackerParameterSlot, self).read(f)
        read_assert_tag(f, 0x02)
        read_assert_tag(f, 0x01)
        size = read_s16le(f)
        assert size >= 0
        self.settings = bytearray(f.read(size))

        count = read_s32le(f)
        assert count >= 0
        self.params = AVBRefList(self.root)
        for i in range(count):
            ref = read_object_ref(self.root, f)
            self.params.append(ref)

        read_assert_tag(f, 0x03)

@utils.register_class
class TrackerData(core.AVBObject):
    class_id = b'TKDA'
    propertydefs = [
        AVBPropertyDef('settings',        'OMFI:TKDA:TrackerSettings',            'bytes'),
        AVBPropertyDef('clip_version',    'OMFI:TKDA:TrackerClipVersion',         'uint32'),
        AVBPropertyDef('clips',           'OMFI:TKDA:TrackerClip',                'ref_list'),
        AVBPropertyDef('offset_tracking', 'OMFI:TKDA:TrackerOffsetTracking',      'uint32'),
        AVBPropertyDef('smoothing',       'OMFI:TKDA:TrackerSmoothing',           'uint32'),
        AVBPropertyDef('jitter_removal',  'name="OMFI:TKDA:TrackerJitterRemoval', 'uint32'),
        AVBPropertyDef('filter_amount',  'name="OMFI:TKDA:TrackerFilterDataAmt',  'double'),
        AVBPropertyDef('clip5',           'OMFI:TKDA:TrackerClip',                'reference'),
        AVBPropertyDef('clip6',           'OMFI:TKDA:TrackerClip',                'reference'),
    ]
    __slots__ = ()

    def read(self, f):
        super(TrackerData, self).read(f)
        read_assert_tag(f, 0x02)
        read_assert_tag(f, 0x01)

        setting_size = read_s16le(f)
        self.settings = bytearray(f.read(setting_size))
        self.clip_version = read_u32le(f)

        count = read_s16le(f)
        self.clips = AVBRefList(self.root)
        for i in range(count):
            ref = read_object_ref(self.root, f)
            self.clips.append(ref)

        for tag in iter_ext(f):
            if tag == 0x01:
                read_assert_tag(f, 72)
                self.offset_tracking = read_u32le(f)
            elif tag == 0x02:
                read_assert_tag(f, 72)
                self.smoothing = read_u32le(f)
            elif tag == 0x03:
                read_assert_tag(f, 72)
                self.jitter_removal = read_u32le(f)
            elif tag == 0x04:
                read_assert_tag(f, 75)
                self.filter_amount = read_doublele(f)
            elif tag == 0x05:
                read_assert_tag(f, 72)
                ref = read_object_ref(self.root, f)
                self.clip5 = ref
            elif tag == 0x06:
                read_assert_tag(f, 72)
                ref = read_object_ref(self.root, f)
                self.clip6 = ref
            else:
                raise ValueError("%s: unknown ext tag 0x%02X %d" % (str(self.class_id), tag,tag))

        read_assert_tag(f, 0x03)


@utils.register_class
class TrackerParameter(core.AVBObject):
    class_id = b'TKPA'
    propertydefs = [
        AVBPropertyDef('settings', 'OMFI:TKPA:ParamSettings','bytes'),
    ]
    __slots__ = ()

    def read(self, f):
        super(TrackerParameter, self).read(f)
        read_assert_tag(f, 0x02)
        read_assert_tag(f, 0x01)
        size = read_s16le(f)
        assert size >= 0
        self.settings = bytearray(f.read(size))

        read_assert_tag(f, 0x03)
