from __future__ import (
    unicode_literals,
    absolute_import,
    print_function,
    division,
    )

from . import core
from . import utils
from .core import AVBProperty
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

@utils.register_class
class FileLocator(core.AVBObject):
    class_id = b'FILE'
    properties = [
        AVBProperty('path_name', 'OMFI:FL:PathName', 'string'),
        AVBProperty('paths',     'OMFI:FL:Paths',     'list'),
    ]

    def read(self, f):
        super(FileLocator, self).read(f)

        tag = read_byte(f)
        version = read_byte(f)

        assert tag == 0x02
        assert version == 2
        self.paths = []
        path = read_string(f)
        if path:
            self.path_name= path

        for tag in iter_ext(f):
            if tag == 0x01:
                read_assert_tag(f, 76)
                path = read_string(f)
                if path:
                    self.paths.append(path)

            elif tag == 0x02:
                read_assert_tag(f, 76)
                # utf-8?
                path = read_string(f)
                if path:
                    self.paths.append(path)
            else:
                raise ValueError("%s: unknown ext tag 0x%02X %d" % (str(self.class_id), tag,tag))

        tag = read_byte(f)
        assert tag == 0x03

@utils.register_class
class GraphicEffect(core.AVBObject):
    class_id = b'GRFX'
    properties = [
        AVBProperty('pict_data', 'OMFI:MC:GRFX:PictData', 'bytes'),
    ]
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
    properties = [
        AVBProperty('percent_time',     'OMFI:FXPS:percentTime',         'int32'),
        AVBProperty('level',            'OMFI:FXPS:level',               'int32'),
        AVBProperty('pos_x',            'OMFI:FXPS:posX',                'int32'),
        AVBProperty('floor_x',          'OMFI:FXPS:xFloor',              'int32'),
        AVBProperty('ceil_x',           'OMFI:FXPS:xCeiling',            'int32'),
        AVBProperty('pos_y',            'OMFI:FXPS:posY',                'int32'),
        AVBProperty('floor_y',          'OMFI:FXPS:yFloor',              'int32'),
        AVBProperty('ceil_y',           'OMFI:FXPS:yCeiling',            'int32'),
        AVBProperty('scale_x',          'OMFI:FXPS:xScale',              'int32'),
        AVBProperty('scale_y',          'OMFI:FXPS:yScale',              'int32'),
        AVBProperty('crop_left',        'OMFI:FXPS:cropLeft',            'int32'),
        AVBProperty('crop_right',       'OMFI:FXPS:cropRight',           'int32'),
        AVBProperty('crop_top',         'OMFI:FXPS:cropTop',             'int32'),
        AVBProperty('crop_bottom',      'OMFI:FXPS:cropBottom',          'int32'),
        AVBProperty('box',              'OMFI:FXPS:box',                 'list'),
        AVBProperty('box_xscale',       'OMFI:FXPS:boxLvl2Xscale',       'bool'),
        AVBProperty('box_yscale',       'OMFI:FXPS:boxLvl2Yscale',       'bool'),
        AVBProperty('box_xpos',         'OMFI:FXPS:FXboxLvl2Xpos',       'bool'),
        AVBProperty('box_ypos',         'OMFI:FXPS:omFXboxLvl2Ypos',     'bool'),
        AVBProperty('border_width',     'OMFI:FXPS:borderWidth',         'int32'),
        AVBProperty('border_soft',      'OMFI:FXPS:borderSoft',          'int32'),
        AVBProperty('splill_gain2',     'OMFI:FXPS:spillSecondGain',     'int16'),
        AVBProperty('splill_gain',      'OMFI:FXPS:spillGain',           'int16'),
        AVBProperty('splill_soft2',     'OMFI:FXPS:spillSecondSoft',     'int16'),
        AVBProperty('splill_soft',      'OMFI:FXPS:spillSoft',           'int16'),
        AVBProperty('enable_key_flags', 'OMFI:FXPS:enableKeyFlags',      'int8'),
        AVBProperty('colors',           'OMFI:FXPS:Colors',              'list'),
        AVBProperty('user_param',       'OMFI:FXPS:userParam',           'bytes'),
        AVBProperty('selected',         'OMFI:FXPS:selected',            'bool'),
    ]

@utils.register_class
class EffectParamList(core.AVBObject):
    class_id = b'FXPS'
    properties = [
        AVBProperty('orig_length',   'OMFI:FXPS:originalLength',   'int32'),
        AVBProperty('window_offset', 'OMFI:FXPS:omFXwindowOffset', 'int32'),
        AVBProperty('keyframe_size', 'OMFI:FXPS:keyFrameSize',     'int32'),
    ]
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
    properties = [
        AVBProperty('byte_order', 'OMFI:AVUP:ByteOrder', 'uint16'),
        AVBProperty('uuid',       'OMFI:AVUP:TypeID',    'UUID'),
        AVBProperty('data',       'OMFI:AVUP:ValueData', 'bytes'),
    ]

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
    properties = [
        AVBProperty('uuid',            'OMFI:PRIT:GUID',                   'UUID'),
        AVBProperty('value_type',      'OMFI:PRIT:ValueType',              'int16'),
        AVBProperty('value',           'OMFI:PRIT:Value',                  'int32'),
        AVBProperty('name',            'OMFI:PRIT:Name',                   'string'),
        AVBProperty('enable',          'OMFI:PRIT:Enabled',                'bool'),
        AVBProperty('control_track',   'OMFI:PRIT:ControlTrack',           'reference'),
        AVBProperty('contribs_to_sig', 'OMFI:PRIT:ContributesToSignature', 'bool'),
    ]

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
    properties = [
        AVBProperty('last_known_volume', 'OMFI:MSML:LastKnownVolume', 'string'),
        AVBProperty('domain_type',       'OMFI:MSML:DomainType',      'int32'),
        AVBProperty('mob_id',            'MobID',                     'MobID'),
    ]
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
                length = read_s16le(f)
                assert length >= 0
                last_known_volume_utf8 = f.read(length)
            else:
                raise ValueError("%s: unknown ext tag 0x%02X %d" % (str(self.class_id), tag,tag))

        read_assert_tag(f, 0x03)

@utils.register_class
class Position(core.AVBObject):
    class_id = b'APOS'
    properties = [
        AVBProperty('mob_id', "MobID", 'MobID'),
    ]

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
    properties = Position.properties + [
        AVBProperty('sample_num',  "__OMFI:MSBO:sampleNum",   'int32'),
        AVBProperty('length',      "__OMFI:MSBO:length",      'int32'),
        AVBProperty('track_type',  "OMFI:trkt:Track.trkType", 'int32'),
        AVBProperty('track_index', "OMFI:trkt:Track.trkLNum", 'int32'),
    ]
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
    properties = BOBPosition.properties + [
        AVBProperty('strip',        "_Strip",       'int32'),
        AVBProperty('offset',       "_Offset",      'uint64'),
        AVBProperty('byte_length',  "_ByteLength",  'uint64'),
        AVBProperty('spos_invalid', "_SPosInvalid", 'bool'),
    ]

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
    properties = [
        AVBProperty('uid_high', 'OMFI:MCBR:MC:binID.high', 'int32'),
        AVBProperty('uid_low',  'OMFI:MCBR:MC:binID.low',  'int32'),
        AVBProperty('name',     'OMFI:MCBR:MC:binName',    'string'),
    ]
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
                length = read_s16le(f)
                assert length >= 0
                # always starts with '\x00\x00' ??
                name_utf8 = f.read(length)

            else:
                raise ValueError("%s: unknown ext tag 0x%02X %d" % (str(self.class_id), tag,tag))

        read_assert_tag(f, 0x03)

@utils.register_class
class MobRef(core.AVBObject):
    class_id = b'MCMR'
    properties = [
            AVBProperty('position',      'OMFI:MCMR:MC:Position', 'int32'),
            AVBProperty('mob_id',        'MobID', 'MobID'),
    ]
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
    properties = MobRef.properties + [
        AVBProperty('comp_offset',   'OMFI:TMBC:MC:CompOffset',             'int32'),
        AVBProperty('attributes',    'OMFI:TMBC:MC:Attributes',             'reference'),
        AVBProperty('color',         'OMFI:TMBC:MC:CarbonAPI::RGBColor',    'list'),
        AVBProperty('handled_codes', 'OMFI:TMBC:MC:handledBadControlCodes', 'bool'),
    ]

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
        self.color.append(read_s16le(f))
        self.color.append(read_s16le(f))
        self.color.append(read_s16le(f))

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
    properties = [
        AVBProperty('data_slots',  'OMFI:TKMN:TrackerDataSlots',  'reference'),
        AVBProperty('param_slots', 'OMFI:TKMN:TrackedParamSlots', 'reference'),
    ]

    def read(self, f):
        super(TrackerManager, self).read(f)
        read_assert_tag(f, 0x02)
        read_assert_tag(f, 0x01)

        self.data_slots = read_object_ref(self.root, f)
        self.param_slots = read_object_ref(self.root, f)

        read_assert_tag(f, 0x03)
