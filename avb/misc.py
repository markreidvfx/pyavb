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
from . utils import peek_data

class FileLocator(core.AVBObject):
    class_id = b'FILE'
    propertydefs_dict = {}
    propertydefs = [
        AVBPropertyDef('path',        'OMFI:FL:PathName',       'string'),
        AVBPropertyDef('path_posix',  'OMFI:FL:POSIXPathName',  'string'),
        AVBPropertyDef('path_utf8',   'OMFI:FL:PathNameUTF8',   'string'),
        AVBPropertyDef('path2_utf8',  'OMFI:FL:PathNameUTF8',   'string')
    ]
    __slots__ = ()

    def read(self, f):
        super(FileLocator, self).read(f)
        ctx = self.root.ictx
        ctx.read_assert_tag(f, 0x02)
        ctx.read_assert_tag(f, 0x02)

        self.path = ctx.read_string(f)

        for tag in ctx.iter_ext(f):
            if tag == 0x01:
                ctx.read_assert_tag(f, 76)
                self.path_posix = ctx.read_string(f)
            elif tag == 0x02:
                ctx.read_assert_tag(f, 76)
                self.path_utf8 = ctx.read_string(f, 'utf-8')
            elif tag == 0x03:
                ctx.read_assert_tag(f, 76)
                self.path2_utf8 = ctx.read_string(f, 'utf-8')
            else:
                raise ValueError("%s: unknown ext tag 0x%02X %d" % (str(self.class_id), tag,tag))

        ctx.read_assert_tag(f, 0x03)

    def write(self, f):
        super(FileLocator, self).write(f)
        ctx = self.root.octx
        ctx.write_u8(f, 0x02)
        ctx.write_u8(f, 0x02)

        ctx.write_string(f, self.path)

        if hasattr(self, 'path_posix'):
            ctx.write_u8(f, 0x01)
            ctx.write_u8(f, 0x01)
            ctx.write_u8(f, 76)
            ctx.write_string(f, self.path_posix)

        if hasattr(self, 'path_utf8'):
            ctx.write_u8(f, 0x01)
            ctx.write_u8(f, 0x02)
            ctx.write_u8(f, 76)
            ctx.write_string(f, self.path_utf8, encoding='utf-8')

        if hasattr(self, 'path2_utf8'):
            ctx.write_u8(f, 0x01)
            ctx.write_u8(f, 0x03)
            ctx.write_u8(f, 76)
            ctx.write_string(f, self.path2_utf8, encoding='utf-8')

        ctx.write_u8(f, 0x03)

@utils.register_class
class MacFileLocator(FileLocator):
    class_id = b'FILE'
    propertydefs_dict = {}
    __slots__ = ()

@utils.register_class
class WinFileLocator(FileLocator):
    class_id = b'WINF'
    propertydefs_dict = {}
    __slots__ = ()

@utils.register_class
class URLLocator(core.AVBObject):
    class_id = b'URLL'
    propertydefs_dict = {}
    __slots__ = ()

    def read(self, f):
        super(URLLocator, self).read(f)
        ctx = self.root.ictx
        ctx.read_assert_tag(f, 0x03)

    def write(self, f):
        super(URLLocator, self).write(f)
        ctx = self.root.octx
        ctx.write_u8(f, 0x03)

@utils.register_class
class GraphicEffect(core.AVBObject):
    class_id = b'GRFX'
    propertydefs_dict = {}
    propertydefs = [
        AVBPropertyDef('pict_data', 'OMFI:MC:GRFX:PictData', 'bytes'),
    ]
    __slots__ = ()

    def read(self, f):
        super(GraphicEffect, self).read(f)
        ctx = self.root.ictx
        ctx.read_assert_tag(f, 0x02)
        ctx.read_assert_tag(f, 0x01)

        pict_size = ctx.read_s32(f)
        assert pict_size >= 0

        self.pict_data = bytearray(f.read(pict_size))
        assert len(self.pict_data) == pict_size

        ctx.read_assert_tag(f, 0x03)

    def write(self, f):
        super(GraphicEffect, self).write(f)
        ctx = self.root.octx
        ctx.write_u8(f, 0x02)
        ctx.write_u8(f, 0x01)

        ctx.write_s32(f, len(self.pict_data))
        f.write(self.pict_data)

        ctx.write_u8(f, 0x03)

@utils.register_class
class ShapeList(core.AVBObject):
    class_id = b'SHLP'
    propertydefs_dict = {}
    propertydefs = [
        AVBPropertyDef('shape_data', 'ShapeList', 'bytes'),
    ]

    def read(self, f):
        super(ShapeList, self).read(f)
        ctx = self.root.ictx
        ctx.read_assert_tag(f, 0x02)
        ctx.read_assert_tag(f, 0x01)

        data_size = ctx.read_s32(f)
        assert data_size >= 0

        self.shape_data = bytearray(f.read(data_size))
        assert len(self.shape_data) == data_size
        ctx.read_assert_tag(f, 0x03)

    def write(self, f):
        super(ShapeList, self).write(f)
        ctx = self.root.octx
        ctx.write_u8(f, 0x02)
        ctx.write_u8(f, 0x01)

        ctx.write_s32(f, len(self.shape_data))
        f.write(self.shape_data)

        ctx.write_u8(f, 0x03)

@utils.register_class
class ColorCorrectionEffect(core.AVBObject):
    class_id = b'CCFX'
    propertydefs_dict = {}
    propertydefs = [
        AVBPropertyDef('color_correction', 'OMFI:FXPS:colorCorrection', 'bytes'),
    ]
    __slots__ = ()

    def read(self, f):
        super(ColorCorrectionEffect, self).read(f)
        ctx = self.root.ictx
        ctx.read_assert_tag(f, 0x02)
        ctx.read_assert_tag(f, 0x01)

        data_size = ctx.read_s16(f)
        assert data_size >= 0
        #
        self.color_correction = bytearray(f.read(data_size))
        assert len(self.color_correction) == data_size
        ctx.read_assert_tag(f, 0x03)

    def write(self, f):
        super(ColorCorrectionEffect, self).write(f)
        ctx = self.root.octx
        ctx.write_u8(f, 0x02)
        ctx.write_u8(f, 0x01)

        ctx.write_s16(f, len(self.color_correction))
        f.write(self.color_correction)

        ctx.write_u8(f, 0x03)

@utils.register_helper_class
class EffectParam(core.AVBObject):
    propertydefs_dict = {}
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
    propertydefs_dict = {}
    propertydefs = [
        AVBPropertyDef('orig_length',   'OMFI:FXPS:originalLength',   'int32'),
        AVBPropertyDef('window_offset', 'OMFI:FXPS:omFXwindowOffset', 'int32'),
        AVBPropertyDef('keyframe_size', 'OMFI:FXPS:keyFrameSize',     'int32'),
        AVBPropertyDef('parameters',   'paramamters',                 'list'),
    ]
    __slots__ = ()

    def read(self, f):
        super(EffectParamList, self).read(f)
        ctx = self.root.ictx
        ctx.read_assert_tag(f, 0x02)
        ctx.read_assert_tag(f, 0x12)

        self.orig_length = ctx.read_s32(f)
        self.window_offset = ctx.read_s32(f)

        count = ctx.read_s32(f)
        self.keyframe_size = ctx.read_s32(f)
        self.parameters = []

        for i in range(count):
            p = EffectParam.__new__(EffectParam, root=self.root)
            start = f.tell()
            p.percent_time = ctx.read_s32(f)
            p.level = ctx.read_s32(f)
            p.pos_x = ctx.read_s32(f)
            p.floor_x = ctx.read_s32(f)
            p.ceil_x = ctx.read_s32(f)
            p.pos_y = ctx.read_s32(f)
            p.floor_y = ctx.read_s32(f)
            p.ceil_y = ctx.read_s32(f)
            p.scale_x = ctx.read_s32(f)
            p.scale_y = ctx.read_s32(f)

            p.crop_left = ctx.read_s32(f)
            p.crop_right = ctx.read_s32(f)
            p.crop_top = ctx.read_s32(f)
            p.crop_bottom = ctx.read_s32(f)

            p.box = []
            # boxTop
            p.box.append(ctx.read_s32(f))
            # boxBottom
            p.box.append(ctx.read_s32(f))
            # boxTop repeat??
            p.box.append(ctx.read_s32(f))
            # boxRight
            p.box.append(ctx.read_s32(f))

            p.box_xscale = ctx.read_bool(f)
            p.box_yscale = ctx.read_bool(f)
            p.box_xpos = ctx.read_bool(f)
            p.box_ypos = ctx.read_bool(f)

            p.border_width = ctx.read_s32(f)
            p.border_soft = ctx.read_s32(f)

            p.splill_gain2 = ctx.read_s16(f)
            p.splill_gain = ctx.read_s16(f)
            p.splill_soft2 = ctx.read_s16(f)
            p.splill_soft = ctx.read_s16(f)

            p.enable_key_flags = ctx.read_s8(f)

            p.colors = []
            color_count = ctx.read_s32(f)
            assert color_count >= 0
            for j in range(color_count):
                color = ctx.read_s32(f)
                p.colors.append(color)

            param_size = ctx.read_s32(f)
            assert param_size >= 0

            p.user_param = bytearray(f.read(param_size))
            p.selected = ctx.read_bool(f)

            self.parameters.append(p)

        ctx.read_assert_tag(f, 0x03)

    def write(self, f):
        super(EffectParamList, self).write(f)
        ctx = self.root.octx
        ctx.write_u8(f, 0x02)
        ctx.write_u8(f, 0x12)

        ctx.write_s32(f, self.orig_length)
        ctx.write_s32(f, self.window_offset)

        ctx.write_s32(f, len(self.parameters))
        ctx.write_s32(f, self.keyframe_size)

        for p in self.parameters:

            ctx.write_s32(f, p.percent_time)
            ctx.write_s32(f, p.level)
            ctx.write_s32(f, p.pos_x)
            ctx.write_s32(f, p.floor_x)
            ctx.write_s32(f, p.ceil_x)
            ctx.write_s32(f, p.pos_y)
            ctx.write_s32(f, p.floor_y)
            ctx.write_s32(f, p.ceil_y)
            ctx.write_s32(f, p.scale_x)
            ctx.write_s32(f, p.scale_y)

            ctx.write_s32(f, p.crop_left)
            ctx.write_s32(f, p.crop_right)
            ctx.write_s32(f, p.crop_top)
            ctx.write_s32(f, p.crop_bottom)

            # boxTop
            ctx.write_s32(f, p.box[0])
            # boxBottom
            ctx.write_s32(f, p.box[1])
            # boxTop repeat??
            ctx.write_s32(f, p.box[2])
            # boxRight
            ctx.write_s32(f, p.box[3])

            ctx.write_bool(f, p.box_xscale)
            ctx.write_bool(f, p.box_yscale)
            ctx.write_bool(f, p.box_xpos)
            ctx.write_bool(f, p.box_ypos)

            ctx.write_s32(f, p.border_width)
            ctx.write_s32(f, p.border_soft)

            ctx.write_s16(f, p.splill_gain2)
            ctx.write_s16(f, p.splill_gain)
            ctx.write_s16(f, p.splill_soft2)
            ctx.write_s16(f, p.splill_soft)

            ctx.write_s8(f, p.enable_key_flags)

            ctx.write_s32(f, len(p.colors))

            for color in p.colors:
                ctx.write_s32(f, color)

            ctx.write_s32(f, len(p.user_param))
            f.write(p.user_param)
            ctx.write_bool(f, p.selected)

        ctx.write_u8(f, 0x03)

@utils.register_class
class CFUserParam(core.AVBObject):
    class_id = b'AVUP'
    propertydefs_dict = {}
    propertydefs = [
        AVBPropertyDef('byte_order', 'OMFI:AVUP:ByteOrder', 'uint16'),
        AVBPropertyDef('uuid',       'OMFI:AVUP:TypeID',    'UUID'),
        AVBPropertyDef('data',       'OMFI:AVUP:ValueData', 'bytes'),
    ]
    __slots__ = ()

    def read(self, f):
        super(CFUserParam, self).read(f)
        ctx = self.root.ictx
        ctx.read_assert_tag(f, 0x02)
        ctx.read_assert_tag(f, 0x01)

        self.byte_order = ctx.read_s16(f)
        assert self.byte_order == 0x4949

        self.uuid = ctx.read_raw_uuid(f)

        # why twice?
        value_size1 = ctx.read_s32(f)
        value_size2 = ctx.read_s32(f)

        assert value_size2 == (value_size1 - 4)

        self.data = bytearray(f.read(value_size2))

        ctx.read_assert_tag(f, 0x03)

    def write(self, f):
        super(CFUserParam, self).write(f)
        ctx = self.root.octx
        ctx.write_u8(f, 0x02)
        ctx.write_u8(f, 0x01)

        ctx.write_s16(f, 0x4949)

        ctx.write_raw_uuid(f, self.uuid)

        ctx.write_s32(f, len(self.data) + 4)
        ctx.write_s32(f, len(self.data))

        f.write(self.data)

        ctx.write_u8(f, 0x03)

@utils.register_class
class ParameterItems(core.AVBObject):
    class_id = b'PRIT'
    propertydefs_dict = {}
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
        ctx = self.root.ictx
        ctx.read_assert_tag(f, 0x02)
        ctx.read_assert_tag(f, 0x02)

        self.uuid = ctx.read_raw_uuid(f)
        self.value_type = ctx.read_s16(f)
        if self.value_type == 1:
            self.value = ctx.read_s32(f)
        elif self.value_type == 2:
            self.value = ctx.read_double(f)
        elif self.value_type == 4:
            self.value = ctx.read_object_ref(self.root, f)
        else:
            raise ValueError("unknown value_type: %d" % self.value_type)

        self.name = ctx.read_string(f)
        self.enable = ctx.read_bool(f)
        self.control_track = ctx.read_object_ref(self.root, f)

        for tag in ctx.iter_ext(f):
            if tag == 0x01:
                ctx.read_assert_tag(f, 66)
                self.contribs_to_sig = ctx.read_bool(f)
            else:
                raise ValueError("%s: unknown ext tag 0x%02X %d" % (str(self.class_id), tag,tag))

        ctx.read_assert_tag(f, 0x03)

    def write(self, f):
        super(ParameterItems, self).write(f)
        ctx = self.root.octx
        ctx.write_u8(f, 0x02)
        ctx.write_u8(f, 0x02)

        ctx.write_raw_uuid(f, self.uuid)
        ctx.write_s16(f, self.value_type)

        if self.value_type == 1:
            ctx.write_s32(f, self.value)
        elif self.value_type == 2:
            ctx.write_double(f, self.value)
        elif self.value_type == 4:
            ctx.write_object_ref(self.root, f, self.value)
        else:
            raise ValueError("unknown value_type: %d" % self.value_type)

        if self.name:
            ctx.write_string(f, self.name)
        else:
            ctx.write_u16(f, 0xFFFF)

        ctx.write_bool(f, self.enable)
        ctx.write_object_ref(self.root, f, self.control_track)

        if hasattr(self, 'contribs_to_sig'):
            ctx.write_u8(f, 0x01)
            ctx.write_u8(f, 0x01)
            ctx.write_u8(f, 66)
            ctx.write_bool(f, self.contribs_to_sig)

        ctx.write_u8(f, 0x03)

@utils.register_class
class MSMLocator(core.AVBObject):
    class_id = b'MSML'
    propertydefs_dict = {}
    propertydefs = [
        AVBPropertyDef('last_known_volume',        'OMFI:MSML:LastKnownVolume',      'string'),
        AVBPropertyDef('domain_type',              'OMFI:MSML:DomainType',           'int32'),
        AVBPropertyDef('mob_id',                   'MobID',                          'MobID'),
        AVBPropertyDef('last_known_volume_utf8',   'OMFI:MSML:LastKnownVolumeUTF8', 'string'),
    ]
    __slots__ = ()

    def read(self, f):
        super(MSMLocator, self).read(f)
        ctx = self.root.ictx
        ctx.read_assert_tag(f, 0x02)
        ctx.read_assert_tag(f, 0x02)

        mob_id_hi = ctx.read_u32(f)
        mob_id_lo = ctx.read_u32(f)

        self.last_known_volume = ctx.read_string(f)

        for tag in ctx.iter_ext(f):

            if tag == 0x01:
                ctx.read_assert_tag(f, 71)
                self.domain_type = ctx.read_s32(f)
            elif tag == 0x02:
                self.mob_id = ctx.read_mob_id(f)
            elif tag == 0x03:
                ctx.read_assert_tag(f, 76)
                self.last_known_volume_utf8 = ctx.read_string(f, 'utf-8')
            else:
                raise ValueError("%s: unknown ext tag 0x%02X %d" % (str(self.class_id), tag,tag))

        ctx.read_assert_tag(f, 0x03)

    def write(self, f):
        super(MSMLocator, self).write(f)
        ctx = self.root.octx
        ctx.write_u8(f, 0x02)
        ctx.write_u8(f, 0x02)

        lo = self.mob_id.material.time_low
        hi = self.mob_id.material.time_mid + (self.mob_id.material.time_hi_version << 16)
        ctx.write_u32(f, lo)
        ctx.write_u32(f, hi)

        ctx.write_string(f, self.last_known_volume)

        if hasattr(self, 'domain_type'):
            ctx.write_u8(f, 0x01)
            ctx.write_u8(f, 0x01)
            ctx.write_u8(f, 71)
            ctx.write_s32(f, self.domain_type)

        if hasattr(self, 'mob_id'):
            ctx.write_u8(f, 0x01)
            ctx.write_u8(f, 0x02)
            ctx.write_mob_id(f, self.mob_id)

        if hasattr(self, 'last_known_volume_utf8'):
            ctx.write_u8(f, 0x01)
            ctx.write_u8(f, 0x03)
            ctx.write_u8(f, 76)
            ctx.write_string(f, self.last_known_volume_utf8, 'utf-8')

        ctx.write_u8(f, 0x03)

@utils.register_class
class Position(core.AVBObject):
    class_id = b'APOS'
    propertydefs_dict = {}
    propertydefs = [
        AVBPropertyDef('mob_id', "MobID", 'MobID'),
    ]
    __slots__ = ()

    def read(self, f):
        super(Position, self).read(f)
        ctx = self.root.ictx
        ctx.read_assert_tag(f, 0x02)
        ctx.read_assert_tag(f, 0x01)

        mob_id_hi = ctx.read_u32(f)
        mob_id_lo = ctx.read_u32(f)

        for tag in ctx.iter_ext(f):
            if tag == 0x01:
                self.mob_id = ctx.read_mob_id(f)
            else:
                raise ValueError("%s: unknown ext tag 0x%02X %d" % (str(self.class_id), tag,tag))

        if self.class_id[:] ==  b'APOS':
            ctx.read_assert_tag(f, 0x03)

    def write(self, f):
        super(Position, self).write(f)
        ctx = self.root.octx
        ctx.write_u8(f, 0x02)
        ctx.write_u8(f, 0x01)

        lo = self.mob_id.material.time_low
        hi = self.mob_id.material.time_mid + (self.mob_id.material.time_hi_version << 16)
        ctx.write_u32(f, lo)
        ctx.write_u32(f, hi)

        if hasattr(self, 'mob_id'):
            ctx.write_u8(f, 0x01)
            ctx.write_u8(f, 0x01)
            ctx.write_mob_id(f, self.mob_id)

        if self.class_id[:] ==  b'APOS':
            ctx.write_u8(f, 0x03)

@utils.register_class
class BOBPosition(Position):
    class_id = b'ABOB'
    propertydefs_dict = {}
    propertydefs = Position.propertydefs + [
        AVBPropertyDef('sample_num',  "__OMFI:MSBO:sampleNum",   'int32'),
        AVBPropertyDef('length',      "__OMFI:MSBO:length",      'int32'),
        AVBPropertyDef('track_type',  "OMFI:trkt:Track.trkType", 'int32'),
        AVBPropertyDef('track_index', "OMFI:trkt:Track.trkLNum", 'int32'),
    ]
    __slots__ = ()

    def read(self, f):
        super(BOBPosition, self).read(f)
        ctx = self.root.ictx
        ctx.read_assert_tag(f, 0x02)
        ctx.read_assert_tag(f, 0x01)

        self.sample_num = ctx.read_s32(f)
        self.length = ctx.read_s32(f)
        self.track_type = ctx.read_s16(f)
        self.track_index = ctx.read_s16(f)

        if self.class_id[:] ==  b'ABOB':
            ctx.read_assert_tag(f, 0x03)

    def write(self, f):
        super(BOBPosition, self).write(f)
        ctx = self.root.octx
        ctx.write_u8(f, 0x02)
        ctx.write_u8(f, 0x01)

        ctx.write_s32(f, self.sample_num)
        ctx.write_s32(f, self.length)
        ctx.write_s16(f, self.track_type)
        ctx.write_s16(f, self.track_index)

        if self.class_id[:] ==  b'ABOB':
            ctx.write_u8(f, 0x03)

@utils.register_class
class DIDPosition(BOBPosition):
    class_id = b'DIDP'
    propertydefs_dict = {}
    propertydefs = BOBPosition.propertydefs + [
        AVBPropertyDef('strip',        "_Strip",       'int32'),
        AVBPropertyDef('offset',       "_Offset",      'uint64'),
        AVBPropertyDef('byte_length',  "_ByteLength",  'uint64'),
        AVBPropertyDef('spos_invalid', "_SPosInvalid", 'bool'),
    ]
    __slots__ = ()

    def read(self, f):
        super(DIDPosition, self).read(f)
        ctx = self.root.ictx
        ctx.read_assert_tag(f, 0x02)
        ctx.read_assert_tag(f, 0x01)

        self.strip = ctx.read_s32(f)
        self.offset = ctx.read_u64(f)
        self.byte_length = ctx.read_u64(f)
        self.spos_invalid = ctx.read_bool(f)

        if self.class_id[:] == b'DIDP':
            ctx.read_assert_tag(f, 0x03)

    def write(self, f):
        super(DIDPosition, self).write(f)
        ctx = self.root.octx
        ctx.write_u8(f, 0x02)
        ctx.write_u8(f, 0x01)

        ctx.write_s32(f, self.strip)
        ctx.write_u64(f, self.offset)
        ctx.write_u64(f, self.byte_length)
        ctx.write_bool(f, self.spos_invalid)

        if self.class_id[:] == b'DIDP':
            ctx.write_u8(f, 0x03)

@utils.register_class
class MPGPosition(DIDPosition):
    class_id = b'MPGP'
    propertydefs_dict = {}
    propertydefs = DIDPosition.propertydefs + [
     AVBPropertyDef('trailing_discards',    '_trailingDiscards',      'int16'),
     AVBPropertyDef('need_seq_hdr',          '_needSeqHdr',            'Boolean'),
     AVBPropertyDef('leader_length',         'leaderLength',           'int16'),
     AVBPropertyDef('fields', '               leadingDiscardFields',   'list'),
    ]
    __slots__ = ()

    def read(self, f):
        super(MPGPosition, self).read(f)
        ctx = self.root.ictx
        ctx.read_assert_tag(f, 0x02)
        ctx.read_assert_tag(f, 0x01)

        self.trailing_discards = ctx.read_s16(f)
        self.need_seq_hdr = ctx.read_bool(f)
        self.fields = []

        # NOTE: I think leading_discard_fields == 2 * leader_length
        leader_length = ctx.read_s16(f)
        if leader_length > 0:
            leading_discard_fields = ctx.read_s16(f)
            for i in range(leader_length):
                picture_type = ctx.read_u8(f)
                length = ctx.read_u32(f)
                self.fields.append([picture_type, length])

        ctx.read_assert_tag(f, 0x03)

    def write(self, f):
        super(MPGPosition, self).write(f)
        ctx = self.root.octx
        ctx.write_u8(f, 0x02)
        ctx.write_u8(f, 0x01)

        ctx.write_s16(f, self.trailing_discards)
        ctx.write_bool(f, self.need_seq_hdr)

        leader_length = len(self.fields)
        ctx.write_s16(f, leader_length)
        if leader_length > 0:
            ctx.write_s16(f, leader_length*2)

            for picture_type, length in self.fields:
                ctx.write_u8(f, picture_type)
                ctx.write_u32(f, length)

        ctx.write_u8(f, 0x03)

@utils.register_class
class BinRef(core.AVBObject):
    class_id = b'MCBR'
    propertydefs_dict = {}
    propertydefs = [
        AVBPropertyDef('uid_high',  'OMFI:MCBR:MC:binID.high',  'int32'),
        AVBPropertyDef('uid_low',   'OMFI:MCBR:MC:binID.low',   'int32'),
        AVBPropertyDef('name',      'OMFI:MCBR:MC:binName',     'string'),
        AVBPropertyDef('name_utf8', 'OMFI:MCBR:MC:binNameUTF8', 'string'),
    ]
    __slots__ = ()

    def read(self, f):
        super(BinRef, self).read(f)
        ctx = self.root.ictx
        ctx.read_assert_tag(f, 0x02)
        ctx.read_assert_tag(f, 0x01)

        self.uid_high = ctx.read_s32(f)
        self.uid_low = ctx.read_s32(f)
        self.name = ctx.read_string(f)

        for tag in ctx.iter_ext(f):
            if tag == 0x01:
                ctx.read_assert_tag(f, 76)
                self.name_utf8 = ctx.read_string(f,'utf-8')
            else:
                raise ValueError("%s: unknown ext tag 0x%02X %d" % (str(self.class_id), tag,tag))

        ctx.read_assert_tag(f, 0x03)

    def write(self, f):
        super(BinRef, self).write(f)
        ctx = self.root.octx
        ctx.write_u8(f, 0x02)
        ctx.write_u8(f, 0x01)

        ctx.write_s32(f, self.uid_high)
        ctx.write_s32(f, self.uid_low)
        ctx.write_string(f, self.name)

        ctx.write_u8(f, 0x01)
        ctx.write_u8(f, 0x01)
        ctx.write_u8(f, 76)
        ctx.write_string(f, self.name_utf8, 'utf-8')

        ctx.write_u8(f, 0x03)

@utils.register_class
class MobRef(core.AVBObject):
    class_id = b'MCMR'
    propertydefs_dict = {}
    propertydefs = [
            AVBPropertyDef('position',      'OMFI:MCMR:MC:Position', 'int32'),
            AVBPropertyDef('mob_id',        'MobID', 'MobID'),
    ]
    __slots__ = ()

    def read(self, f):
        super(MobRef, self).read(f)
        ctx = self.root.ictx
        ctx.read_assert_tag(f, 0x02)
        ctx.read_assert_tag(f, 0x01)

        mob_hi = ctx.read_u32(f)
        mob_lo = ctx.read_u32(f)
        self.position = ctx.read_s32(f)

        for tag in ctx.iter_ext(f):
            if tag == 0x01:
                self.mob_id = ctx.read_mob_id(f)
            else:
                raise ValueError("%s: unknown ext tag 0x%02X %d" % (str(self.class_id), tag,tag))

        if self.class_id[:] == b'MCMR':
            ctx.read_assert_tag(f, 0x03)

    def write(self, f):
        super(MobRef, self).write(f)
        ctx = self.root.octx
        ctx.write_u8(f, 0x02)
        ctx.write_u8(f, 0x01)

        lo = self.mob_id.material.time_low
        hi = self.mob_id.material.time_mid + (self.mob_id.material.time_hi_version << 16)

        ctx.write_u32(f, lo)
        ctx.write_u32(f, hi)
        ctx.write_s32(f, self.position)

        if hasattr(self, 'mob_id'):
            ctx.write_u8(f, 0x01)
            ctx.write_u8(f, 0x01)
            ctx.write_mob_id(f, self.mob_id)

        if self.class_id[:] == b'MCMR':
            ctx.write_u8(f, 0x03)

# also called a TimeCrumb
@utils.register_class
class Marker(MobRef):
    class_id = b'TMBC'
    propertydefs_dict = {}
    propertydefs = MobRef.propertydefs + [
        AVBPropertyDef('comp_offset',   'OMFI:TMBC:MC:CompOffset',             'int32'),
        AVBPropertyDef('attributes',    'OMFI:TMBC:MC:Attributes',             'reference'),
        AVBPropertyDef('color',         'OMFI:TMBC:MC:CarbonAPI::RGBColor',    'list'),
        AVBPropertyDef('handled_codes', 'OMFI:TMBC:MC:handledBadControlCodes', 'bool'),
    ]
    __slots__ = ()

    def read(self, f):
        super(Marker, self).read(f)
        ctx = self.root.ictx
        ctx.read_assert_tag(f, 0x02)
        ctx.read_assert_tag(f, 0x03)

        self.comp_offset = ctx.read_s32(f)
        self.attributes = ctx.read_object_ref(self.root, f)
        # print(self.comp_offset, self.attributes)

        version = ctx.read_s16(f)
        assert version == 1

        self.color = []
        self.color.append(ctx.read_u16(f))
        self.color.append(ctx.read_u16(f))
        self.color.append(ctx.read_u16(f))

        for tag in ctx.iter_ext(f):

            if tag == 0x01:
                ctx.read_assert_tag(f, 66)
                self.handled_codes = ctx.read_bool(f)
            else:
                raise ValueError("%s: unknown ext tag 0x%02X %d" % (str(self.class_id), tag,tag))

        ctx.read_assert_tag(f, 0x03)

    def write(self, f):
        super(Marker, self).write(f)
        ctx = self.root.octx
        ctx.write_u8(f, 0x02)
        ctx.write_u8(f, 0x03)

        ctx.write_s32(f, self.comp_offset)
        ctx.write_object_ref(self.root, f, self.attributes)

        #version
        ctx.write_s16(f, 1)

        for c in self.color:
            ctx.write_u16(f, c)

        if hasattr(self, 'handled_codes'):
            ctx.write_u8(f, 0x01)
            ctx.write_u8(f, 0x01)
            ctx.write_u8(f, 66)
            ctx.write_bool(f ,self.handled_codes)

        ctx.write_u8(f, 0x03)

@utils.register_class
class TrackerManager(core.AVBObject):
    class_id = b'TKMN'
    propertydefs_dict = {}
    propertydefs = [
        AVBPropertyDef('data_slots',  'OMFI:TKMN:TrackerDataSlots',  'reference'),
        AVBPropertyDef('param_slots', 'OMFI:TKMN:TrackedParamSlots', 'reference'),
    ]
    __slots__ = ()

    def read(self, f):
        super(TrackerManager, self).read(f)
        ctx = self.root.ictx
        ctx.read_assert_tag(f, 0x02)
        ctx.read_assert_tag(f, 0x01)

        self.data_slots = ctx.read_object_ref(self.root, f)
        self.param_slots = ctx.read_object_ref(self.root, f)

        ctx.read_assert_tag(f, 0x03)

    def write(self, f):
        super(TrackerManager, self).write(f)
        ctx = self.root.octx
        ctx.write_u8(f, 0x02)
        ctx.write_u8(f, 0x01)

        ctx.write_object_ref(self.root, f, self.data_slots)
        ctx.write_object_ref(self.root, f, self.param_slots)

        ctx.write_u8(f, 0x03)

@utils.register_class
class TrackerDataSlot(core.AVBObject):
    class_id = b'TKDS'
    propertydefs_dict = {}
    propertydefs = [
        AVBPropertyDef('tracker_data',  'OMFI:TKDS:TrackerData',      'ref_list'),
        AVBPropertyDef('track_fg',      'OMFI:TKDAS:TrackForeground', 'bool'),
    ]
    __slots__ = ()

    def read(self, f):
        super(TrackerDataSlot, self).read(f)
        ctx = self.root.ictx
        ctx.read_assert_tag(f, 0x02)
        ctx.read_assert_tag(f, 0x01)

        count = ctx.read_s32(f)
        self.tracker_data = AVBRefList.__new__(AVBRefList, root=self.root)
        for i in range(count):
            ref = ctx.read_object_ref(self.root, f)
            self.tracker_data.append(ref)

        for tag in ctx.iter_ext(f):
            if tag == 0x01:
                ctx.read_assert_tag(f, 66)
                self.track_fg = ctx.read_bool(f)
            else:
                raise ValueError("%s: unknown ext tag 0x%02X %d" % (str(self.class_id), tag,tag))

        ctx.read_assert_tag(f, 0x03)

    def write(self, f):
        super(TrackerDataSlot, self).write(f)
        ctx = self.root.octx
        ctx.write_u8(f, 0x02)
        ctx.write_u8(f, 0x01)

        ctx.write_s32(f, len(self.tracker_data))

        for track in self.tracker_data:
            ctx.write_object_ref(self.root, f, track)

        if hasattr(self, 'track_fg'):
            ctx.write_u8(f, 0x01)
            ctx.write_u8(f, 0x01)
            ctx.write_u8(f, 66)
            ctx.write_bool(f, self.track_fg)

        ctx.write_u8(f, 0x03)

@utils.register_class
class TrackerParameterSlot(core.AVBObject):
    class_id = b'TKPS'
    propertydefs_dict = {}
    propertydefs = [
        AVBPropertyDef('settings', 'OMFI:TKPS:EffectSettings', 'bytes'),
        AVBPropertyDef('params',   'OMFI:TKPS:TrackedParam',   'ref_list'),
    ]
    __slots__ = ()

    def read(self, f):
        super(TrackerParameterSlot, self).read(f)
        ctx = self.root.ictx
        ctx.read_assert_tag(f, 0x02)
        ctx.read_assert_tag(f, 0x01)
        size = ctx.read_s16(f)
        assert size >= 0
        self.settings = bytearray(f.read(size))

        count = ctx.read_s32(f)
        assert count >= 0
        self.params = AVBRefList.__new__(AVBRefList, root=self.root)
        for i in range(count):
            ref = ctx.read_object_ref(self.root, f)
            self.params.append(ref)

        ctx.read_assert_tag(f, 0x03)

    def write(self, f):
        super(TrackerParameterSlot, self).write(f)
        ctx = self.root.octx
        ctx.write_u8(f, 0x02)
        ctx.write_u8(f, 0x01)

        ctx.write_s16(f, len(self.settings))
        f.write(self.settings)

        ctx.write_s32(f, len(self.params))
        for p in self.params:
            ctx.write_object_ref(self.root, f, p)

        ctx.write_u8(f, 0x03)

@utils.register_class
class TrackerData(core.AVBObject):
    class_id = b'TKDA'
    propertydefs_dict = {}
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
        ctx = self.root.ictx
        ctx.read_assert_tag(f, 0x02)
        ctx.read_assert_tag(f, 0x01)

        setting_size = ctx.read_s16(f)
        self.settings = bytearray(f.read(setting_size))
        self.clip_version = ctx.read_u32(f)

        count = ctx.read_s16(f)
        self.clips = AVBRefList.__new__(AVBRefList, root=self.root)
        for i in range(count):
            ref = ctx.read_object_ref(self.root, f)
            self.clips.append(ref)

        for tag in ctx.iter_ext(f):
            if tag == 0x01:
                ctx.read_assert_tag(f, 72)
                self.offset_tracking = ctx.read_u32(f)
            elif tag == 0x02:
                ctx.read_assert_tag(f, 72)
                self.smoothing = ctx.read_u32(f)
            elif tag == 0x03:
                ctx.read_assert_tag(f, 72)
                self.jitter_removal = ctx.read_u32(f)
            elif tag == 0x04:
                ctx.read_assert_tag(f, 75)
                self.filter_amount = ctx.read_double(f)
            elif tag == 0x05:
                ctx.read_assert_tag(f, 72)
                self.clip5 = ctx.read_object_ref(self.root, f)
            elif tag == 0x06:
                ctx.read_assert_tag(f, 72)
                self.clip6 = ctx.read_object_ref(self.root, f)
            else:
                raise ValueError("%s: unknown ext tag 0x%02X %d" % (str(self.class_id), tag,tag))

        ctx.read_assert_tag(f, 0x03)

    def write(self, f):
        super(TrackerData, self).write(f)
        ctx = self.root.octx
        ctx.write_u8(f, 0x02)
        ctx.write_u8(f, 0x01)

        ctx.write_s16(f, len(self.settings))
        f.write(self.settings)

        ctx.write_u32(f, self.clip_version)

        ctx.write_s16(f, len(self.clips))

        for clip in self.clips:
            ctx.write_object_ref(self.root, f, clip)

        if hasattr(self, 'offset_tracking'):
            ctx.write_u8(f, 0x01)
            ctx.write_u8(f, 0x01)
            ctx.write_u8(f, 72)
            ctx.write_u32(f, self.offset_tracking)

        if hasattr(self, 'smoothing'):
            ctx.write_u8(f, 0x01)
            ctx.write_u8(f, 0x02)
            ctx.write_u8(f, 72)
            ctx.write_u32(f, self.smoothing)

        if hasattr(self, 'jitter_removal'):
            ctx.write_u8(f, 0x01)
            ctx.write_u8(f, 0x03)
            ctx.write_u8(f, 72)
            ctx.write_u32(f, self.jitter_removal)

        if hasattr(self, 'filter_amount'):
            ctx.write_u8(f, 0x01)
            ctx.write_u8(f, 0x04)
            ctx.write_u8(f, 75)
            ctx.write_double(f, self.filter_amount)

        if hasattr(self, 'clip5'):
            ctx.write_u8(f, 0x01)
            ctx.write_u8(f, 0x05)
            ctx.write_u8(f, 72)
            ctx.write_object_ref(self.root, f, self.clip5)

        if hasattr(self, 'clip6'):
            ctx.write_u8(f, 0x01)
            ctx.write_u8(f, 0x06)
            ctx.write_u8(f, 72)
            ctx.write_object_ref(self.root, f, self.clip6)

        ctx.write_u8(f, 0x03)


@utils.register_class
class TrackerParameter(core.AVBObject):
    class_id = b'TKPA'
    propertydefs_dict = {}
    propertydefs = [
        AVBPropertyDef('settings', 'OMFI:TKPA:ParamSettings','bytes'),
    ]
    __slots__ = ()

    def read(self, f):
        super(TrackerParameter, self).read(f)
        ctx = self.root.ictx
        ctx.read_assert_tag(f, 0x02)
        ctx.read_assert_tag(f, 0x01)
        size = ctx.read_s16(f)
        assert size >= 0
        self.settings = bytearray(f.read(size))

        ctx.read_assert_tag(f, 0x03)


    def write(self, f):
        super(TrackerParameter, self).write(f)
        ctx = self.root.octx
        ctx.write_u8(f, 0x02)
        ctx.write_u8(f, 0x01)

        ctx.write_s16(f, len(self.settings))
        f.write(self.settings)

        ctx.write_u8(f, 0x03)
