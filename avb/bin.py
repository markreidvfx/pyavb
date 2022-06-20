from __future__ import (
    unicode_literals,
    absolute_import,
    print_function,
    division,
    )

from . import core
from . import utils
from . core import AVBPropertyDef
from . utils import peek_data

class Setting(core.AVBObject):
    class_id = b'ASET'
    propertydefs_dict = {}
    propertydefs = [
        AVBPropertyDef('name',       'name',       'string'),
        AVBPropertyDef('kind',       'kind',       'string'),
        AVBPropertyDef('attr_count', 'attributes', 'int16',      1),
        AVBPropertyDef('attr_type',  'type',       'int16',     20),
        AVBPropertyDef('attributes', 'attrList',   'reference'),
    ]
    __slots__ = ()

    def read(self, f):
        super(Setting, self).read(f)
        ctx = self.root.ictx
        ctx.read_assert_tag(f, 0x02)
        ctx.read_assert_tag(f, 0x06)

        self.name = ctx.read_string(f)
        self.kind = ctx.read_string(f)

        self.attr_count = ctx.read_s16(f)
        self.attr_type =  ctx.read_s16(f)
        self.attributes = ctx.read_object_ref(self.root, f)

    def write(self, f):
        super(Setting, self).write(f)

        ctx = self.root.octx

        ctx.write_u8(f, 0x02)
        ctx.write_u8(f, 0x06)

        ctx.write_string(f, self.name)
        ctx.write_string(f, self.kind)

        ctx.write_s16(f, self.attr_count)
        ctx.write_s16(f, self.attr_type)
        ctx.write_object_ref(self.root, f, self.attributes)

default_bin_columns = [
    {u'title': u'Color',         u'format': 105,  u'type': 51,  u'hidden': False},
    {u'title': u'   ',           u'format': 0,    u'type': 200, u'hidden': False},
    {u'title': u'Name',          u'format': 20,   u'type': 201, u'hidden': False},
    {u'title': u'Creation Date', u'format': 102,  u'type': 12,  u'hidden': False},
    {u'title': u'Duration',      u'format': 100,  u'type': 4,   u'hidden': False},
    {u'title': u'Drive',         u'format': 2,    u'type': 14,  u'hidden': False},
    {u'title': u'IN-OUT',        u'format': 100,  u'type': 7,   u'hidden': False},
    {u'title': u'Mark IN',       u'format': 100,  u'type': 5,   u'hidden': False},
    {u'title': u'Mark OUT',      u'format': 100,  u'type': 6,   u'hidden': False},
    {u'title': u'Tracks',        u'format': 2,    u'type': 1,   u'hidden': False},
    {u'title': u'Start',         u'format': 100,  u'type': 2,   u'hidden': False},
    {u'title': u'Tape',          u'format': 2,    u'type': 8,   u'hidden': False},
    {u'title': u'Video',         u'format': 2,    u'type': 13,  u'hidden': False},
    {u'title': u'Plug-in',       u'format': 2,    u'type': 133, u'hidden': False},
    {u'title': u'TapeID',        u'format': 2,    u'type': 50,  u'hidden': False},
    {u'title': u'Audio SR',      u'format': 2,    u'type': 11,  u'hidden': False},
    {u'title': u'Comments',      u'format': 2,    u'type': 40,  u'hidden': False},
]

@utils.register_class
class BinViewSetting(Setting):
    class_id = b'BVst'
    propertydefs_dict = {}
    propertydefs = Setting.propertydefs + [
        AVBPropertyDef('columns',              'Columns',          'list'),
        AVBPropertyDef('format_descriptors',   'FormatDescriptor', 'list'),
    ]
    __slots__ = ()

    def __init__(self):
        super(BinViewSetting, self).__init__(self)
        self.name = u'Untitled'
        self.kind = u'Bin View'
        self.attributes = self.root.create.Attributes()
        self.format_descriptors = []
        self.columns = []
        self.columns.extend(default_bin_columns)

    def read(self, f):
        super(BinViewSetting, self).read(f)
        ctx = self.root.ictx
        ctx.read_assert_tag(f, 0x02)
        ctx.read_assert_tag(f, 10)

        self.columns = []

        column_count = ctx.read_u16(f)
        for i in range(column_count):
            d = {}
            d['title']  = ctx.read_string(f)
            d['format'] = ctx.read_s16(f)
            d['type']   = ctx.read_s16(f)
            d['hidden'] = ctx.read_bool(f)
            self.columns.append(d)

        for tag in ctx.iter_ext(f):
            if tag == 0x01:
                ctx.read_assert_tag(f, 69)
                num_vcid_free_columns = ctx.read_s16(f)
                assert num_vcid_free_columns >= 0
                self.format_descriptors = []
                for i in range(num_vcid_free_columns):
                    d = {}

                    ctx.read_assert_tag(f, 69)

                    # vcid == Video Codec ID?
                    d['vcid_free_column_id'] = ctx.read_s16(f)

                    ctx.read_assert_tag(f, 71)
                    format_descriptor_size = ctx.read_s32(f)

                    ctx.read_assert_tag(f, 76)

                    # utf-8 seems to start with 4 null bytes
                    ctx.read_s32(f)
                    d['format_descriptor'] = f.read(format_descriptor_size).decode('utf8')
                    self.format_descriptors.append(d)
            else:
                raise ValueError("%s: unknown ext tag 0x%02X %d" % (str(self.class_id), tag,tag))

        ctx.read_assert_tag(f, 0x03)

    def write(self, f):
        super(BinViewSetting, self).write(f)
        ctx = self.root.octx

        ctx.write_u8(f, 0x02)
        ctx.write_u8(f, 10)
        ctx.write_u16(f, len(self.columns))

        for d in self.columns:
            ctx.write_string(f, d['title'])
            ctx.write_s16(f, d['format'])
            ctx.write_s16(f, d['type'])
            ctx.write_bool(f, d['hidden'])

        if hasattr(self, 'format_descriptors'):
            ctx.write_u8(f, 0x01)
            ctx.write_u8(f, 0x01)
            ctx.write_u8(f, 69)
            ctx.write_u16(f, len(self.format_descriptors))

            for d in self.format_descriptors:
                ctx.write_u8(f, 69)
                ctx.write_s16(f, d['vcid_free_column_id'])

                format_data =  d['format_descriptor'].encode('utf-8')
                ctx.write_u8(f, 71)
                ctx.write_s32(f, len(format_data))

                ctx.write_u8(f, 76)
                #null bytes
                ctx.write_s16(f,  len(format_data) + 2)
                ctx.write_s16(f, 0)
                f.write(format_data)

        ctx.write_u8(f, 0x03)

@utils.register_helper_class
class BinItem(core.AVBObject):
    propertydefs_dict = {}
    propertydefs = [
        AVBPropertyDef('mob',         'Composition',  'reference'),
        AVBPropertyDef('x',           'Xpos',         'int16',    -30000),
        AVBPropertyDef('y',           'Ypos',         'int16',    -30000),
        AVBPropertyDef('keyframe',    'Keyframe',     'int32',         0),
        AVBPropertyDef('user_placed', 'userPlaced',   'bool',       True),
    ]
    __slots__ = ()

@utils.register_helper_class
class SiftItem(core.AVBObject):
    propertydefs_dict = {}
    propertydefs = [
        AVBPropertyDef('method', 'SiftMethod', 'int16' ,       1),
        AVBPropertyDef('string', 'SiftString', 'string',     u''),
        AVBPropertyDef('column', 'SiftColumn', 'string',  u'Any'),
    ]
    __slots__ = ()

@utils.register_class
class Bin(core.AVBObject):
    class_id = b'ABIN'
    propertydefs_dict = {}
    propertydefs = [
        AVBPropertyDef('large_bin',         'large_bin',      'bool',     False), #custom
        AVBPropertyDef('view_setting',   'binviewsetting', 'reference'),
        AVBPropertyDef('uid',            'binuid.high',    'uint64'),
        AVBPropertyDef('items',            'Items',          'list',           ), # custom
        AVBPropertyDef('display_mask',     'DisplayMask',    'int32',     98999),
        AVBPropertyDef('display_mode',     'DisplayMode',    'int32',         0),
        AVBPropertyDef('sifted',           'Sifted',         'bool',      False),
        AVBPropertyDef('sifted_settings',  'SiftedSettring', 'list'), #custom
        AVBPropertyDef('sort_columns',     'SortColumns',    'list',           ),
        AVBPropertyDef('mac_font',         'MacFont',        'int16',         1),
        AVBPropertyDef('mac_font_size',    'MacFontSize',    'int16',        11),
        AVBPropertyDef('mac_image_scale',  'MacImageScale',  'int16',         5),
        AVBPropertyDef('home_rect',        'HomeRect',       'rect',       [0, 0 , 300, 600]),
        AVBPropertyDef('background_color', 'BackColor',      'color', [45568, 45568, 45568]),
        AVBPropertyDef('forground_color',  'ForeColor',      'color',    [3328, 3328, 3328]),
        AVBPropertyDef('ql_image_scale',   'QLImageScale',   'int16',         6),
        AVBPropertyDef('attributes',       'BinAttr',        'reference'),
        AVBPropertyDef('was_iconic',       'WasIconic',      'bool',      False),
    ]
    __slots__ = ('mob_dict')

    def __init__(self):
        super(Bin, self).__init__(self)

        self.view_setting = self.root.create.BinViewSetting()
        self.uid = utils.generate_uid()
        self.items = []
        self.sort_columns = []

        self.sifted_settings= []
        for i in range(6):
            s = self.root.create.SiftItem()
            self.sifted_settings.append(s)

        self.attributes = self.root.create.Attributes()

    def read(self, f):
        super(Bin, self).read(f)
        ctx = self.root.ictx
        ctx.read_assert_tag(f, 0x02)

        version = ctx.read_u8(f)
        assert version in (0x0e, 0x0f)
        if version ==  0x0f:
            self.large_bin = True
        else:
            self.large_bin = False

        self.view_setting = ctx.read_object_ref(self.root, f)
        self.uid = ctx.read_u64(f)

        if version == 0x0e:
            object_count = ctx.read_u16(f)
        else:
            #large bin size > max u16
            object_count = ctx.read_u32(f)

        self.items = []

        for i in range(object_count):
            bin_obj = BinItem.__new__(BinItem, root=self.root)
            bin_obj.mob = ctx.read_object_ref(self.root, f)
            bin_obj.x = ctx.read_s16(f)
            bin_obj.y = ctx.read_s16(f)
            bin_obj.keyframe = ctx.read_s32(f)
            bin_obj.user_placed = ctx.read_bool(f)
            self.items.append(bin_obj)

        self.display_mask = ctx.read_s32(f)
        self.display_mode = ctx.read_s16(f)

        # sifted stuff for searching settings bin
        # don't care too much about it at the moment
        self.sifted = ctx.read_bool(f)
        self.sifted_settings= []

        for i in range(6):
            s = SiftItem.__new__(SiftItem, root=self.root)
            s.method = ctx.read_s16(f)
            s.string = ctx.read_string(f)
            s.column = ctx.read_string(f)
            self.sifted_settings.append(s)

        sort_column_count = ctx.read_s16(f)
        self.sort_columns = []
        for i in range(sort_column_count):
            direction = ctx.read_u8(f)
            col = ctx.read_string(f)
            self.sort_columns.append([direction, col])


        self.mac_font = ctx.read_s16(f)
        self.mac_font_size = ctx.read_s16(f)
        self.mac_image_scale = ctx.read_s16(f)

        self.home_rect = ctx.read_rect(f)

        self.background_color = ctx.read_rgb_color(f)
        self.forground_color = ctx.read_rgb_color(f)

        self.ql_image_scale = ctx.read_s16(f)

        self.attributes = ctx.read_object_ref(self.root, f)
        self.was_iconic = ctx.read_bool(f)

        if self.class_id[:] == b'ABIN':
            ctx.read_assert_tag(f, 0x03)

    def write(self, f):
        super(Bin, self).write(f)
        ctx = self.root.octx

        ctx.write_u8(f, 0x02)

        object_count = len(self.items)
        #large bin size > max u16
        if self.large_bin or object_count > 0xffff:
            ctx.write_u8(f,  0x0f)
        else:
            ctx.write_u8(f,  0x0e)

        ctx.write_object_ref(self.root, f, self.view_setting)
        ctx.write_u64(f, self.uid)

        #large bin size > max u16
        if self.large_bin or object_count > 0xffff:
            ctx.write_u32(f, object_count)
        else:
            ctx.write_u16(f, object_count)

        for bin_obj in self.items:
             ctx.write_object_ref(self.root, f, bin_obj.mob)
             ctx.write_s16(f, bin_obj.x)
             ctx.write_s16(f, bin_obj.y)
             ctx.write_s32(f, bin_obj.keyframe)
             ctx.write_u8(f, bin_obj.user_placed)

        ctx.write_s32(f, self.display_mask)
        ctx.write_s16(f, self.display_mode)
        ctx.write_bool(f, self.sifted)

        for i in range(6):
            s = self.sifted_settings[i]
            ctx.write_s16(f, s.method)
            ctx.write_string(f, s.string)
            ctx.write_string(f, s.column)


        ctx.write_s16(f, len(self.sort_columns))

        for col in self.sort_columns:
            ctx.write_u8(f, col[0])
            ctx.write_string(f, col[1])

        ctx.write_s16(f, self.mac_font)
        ctx.write_s16(f, self.mac_font_size)
        ctx.write_s16(f, self.mac_image_scale)

        ctx.write_rect(f, self.home_rect)

        ctx.write_rgb_color(f, self.background_color)
        ctx.write_rgb_color(f, self.forground_color)

        ctx.write_s16(f, self.ql_image_scale)
        ctx.write_object_ref(self.root, f, self.attributes)
        ctx.write_bool(f, self.was_iconic)

        if self.class_id[:] == b'ABIN':
            ctx.write_u8(f, 0x03)

    def build_mob_dict(self):
        self.mob_dict = {}
        for mob in self.mobs:
            self.mob_dict[mob.mob_id] = mob

    def add_mob(self, mob):
        bin_item = self.root.create.BinItem()
        bin_item.mob = mob
        self.items.append(bin_item)

    @property
    def mobs(self):
        for item in self.items:
            yield item.mob

    def toplevel(self):
        for mob in self.mobs:
            if  mob.mob_type in ('CompositionMob', ) and mob.usage_code == 0:
                yield mob

    def compositionmobs(self):
        for mob in self.mobs:
            if  mob.mob_type in ('CompositionMob', ):
                yield mob

    def mastermobs(self):
        for mob in self.mobs:
            if  mob.mob_type in ('MasterMob', ):
                yield mob


@utils.register_class
class BinFirst(Bin):
    class_id = b'BINF'
    propertydefs_dict = {}
    propertydefs = Bin.propertydefs + [
        AVBPropertyDef('unknown_s32', 'unknown_s32', 'int32',  0),
    ]
    __slots__ = ()

    def read(self, f):
        super(BinFirst, self).read(f)
        ctx = self.root.ictx
        ctx.read_assert_tag(f, 0x02)
        ctx.read_assert_tag(f, 0x01)

        self.unknown_s32 = ctx.read_s32(f)

        ctx.read_assert_tag(f, 0x03)

    def write(self, f):
        super(BinFirst, self).write(f)
        ctx = self.root.octx

        ctx.write_u8(f, 0x02)
        ctx.write_u8(f, 0x01)

        ctx.write_s32(f, self.unknown_s32)

        ctx.write_u8(f, 0x03)
