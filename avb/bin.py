from __future__ import (
    unicode_literals,
    absolute_import,
    print_function,
    division,
    )

from . import core
from . import utils

from . core import AVBPropertyDef

from . utils import (
    read_u8,          write_u8,
    read_bool,        write_bool,
    read_s16le,       write_s16le,
    read_u16le,       write_u16le,
    read_u32le,       write_u32le,
    read_s32le,       write_s32le,
    read_u64le,       write_u64le,
    read_string,      write_string,
    read_object_ref,  write_object_ref,
    read_assert_tag,
    iter_ext,
    peek_data,
)

class Setting(core.AVBObject):
    class_id = b'ASET'
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
        read_assert_tag(f, 0x02)
        read_assert_tag(f, 0x06)

        self.name = read_string(f)
        self.kind = read_string(f)

        self.attr_count = read_s16le(f)
        self.attr_type = read_s16le(f)
        self.attributes = read_object_ref(self.root, f)

    def write(self, f):
        super(Setting, self).write(f)
        write_u8(f, 0x02)
        write_u8(f, 0x06)

        write_string(f, self.name)
        write_string(f, self.kind)

        write_s16le(f, self.attr_count)
        write_s16le(f, self.attr_type)
        write_object_ref(self.root, f, self.attributes)

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
        read_assert_tag(f, 0x02)
        read_assert_tag(f, 10)

        self.columns = []

        column_count = read_u16le(f)
        for i in range(column_count):
            d = {}
            d['title'] = read_string(f)
            d['format'] = read_s16le(f)
            d['type'] = read_s16le(f)
            d['hidden'] = read_bool(f)
            self.columns.append(d)

        for tag in iter_ext(f):
            if tag == 0x01:
                read_assert_tag(f, 69)
                num_vcid_free_columns = read_s16le(f)
                assert num_vcid_free_columns >= 0
                self.format_descriptors = []
                for i in range(num_vcid_free_columns):
                    d = {}

                    read_assert_tag(f, 69)

                    # vcid == Video Codec ID?
                    d['vcid_free_column_id'] = read_s16le(f)

                    read_assert_tag(f, 71)
                    format_descriptor_size = read_s32le(f)

                    read_assert_tag(f, 76)

                    # utf-8 seems to start with 4 null bytes
                    read_s32le(f)
                    d['format_descriptor'] = f.read(format_descriptor_size).decode('utf8')
                    self.format_descriptors.append(d)
            else:
                raise ValueError("%s: unknown ext tag 0x%02X %d" % (str(self.class_id), tag,tag))

        read_assert_tag(f, 0x03)

    def write(self, f):
        super(BinViewSetting, self).write(f)
        write_u8(f, 0x02)
        write_u8(f, 10)
        write_u16le(f, len(self.columns))

        for d in self.columns:
            write_string(f, d['title'])
            write_s16le(f, d['format'])
            write_s16le(f, d['type'])
            write_bool(f, d['hidden'])

        if hasattr(self, 'format_descriptors'):
            write_u8(f, 0x01)
            write_u8(f, 0x01)
            write_u8(f, 69)
            write_u16le(f, len(self.format_descriptors))

            for d in self.format_descriptors:
                write_u8(f, 69)
                write_s16le(f, d['vcid_free_column_id'])

                format_data =  d['format_descriptor'].encode('utf-8')
                write_u8(f, 71)
                write_s32le(f, len(format_data))

                write_u8(f, 76)
                #null bytes
                write_s16le(f,  len(format_data) + 2)
                write_s16le(f, 0)
                f.write(format_data)

        write_u8(f, 0x03)

@utils.register_helper_class
class BinItem(core.AVBObject):

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
    propertydefs = [
        AVBPropertyDef('method', 'SiftMethod', 'int16' ,       1),
        AVBPropertyDef('string', 'SiftString', 'string',     u''),
        AVBPropertyDef('column', 'SiftColumn', 'string',  u'Any'),
    ]
    __slots__ = ()

@utils.register_class
class Bin(core.AVBObject):
    class_id = b'ABIN'
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
        read_assert_tag(f, 0x02)

        version = read_u8(f)
        assert version in (0x0e, 0x0f)
        if version ==  0x0f:
            self.large_bin = True
        else:
            self.large_bin = False

        self.view_setting = read_object_ref(self.root, f)
        self.uid = read_u64le(f)

        if version == 0x0e:
            object_count = read_u16le(f)
        else:
            #large bin size > max u16
            object_count = read_u32le(f)

        self.items = []

        for i in range(object_count):
            bin_obj = BinItem.__new__(BinItem, root=self.root)
            bin_obj.mob = read_object_ref(self.root, f)
            bin_obj.x = read_s16le(f)
            bin_obj.y = read_s16le(f)
            bin_obj.keyframe = read_s32le(f)
            bin_obj.user_placed = read_bool(f)
            self.items.append(bin_obj)

        self.display_mask = read_s32le(f)
        self.display_mode = read_s16le(f)

        # sifted stuff for searching settings bin
        # don't care too much about it at the moment
        self.sifted = read_bool(f)
        self.sifted_settings= []

        for i in range(6):
            s = SiftItem.__new__(SiftItem, root=self.root)
            s.method = read_s16le(f)
            s.string = read_string(f)
            s.column = read_string(f)
            self.sifted_settings.append(s)

        sort_column_count =  read_s16le(f)
        self.sort_columns = []
        for i in range(sort_column_count):
            direction = read_u8(f)
            col = read_string(f)
            self.sort_columns.append([direction, col])


        self.mac_font = read_s16le(f)
        self.mac_font_size = read_s16le(f)
        self.mac_image_scale = read_s16le(f)

        self.home_rect = utils.read_rect(f)

        self.background_color = utils.read_rgb_color(f)
        self.forground_color = utils.read_rgb_color(f)

        self.ql_image_scale = read_s16le(f)

        self.attributes = read_object_ref(self.root, f)
        self.was_iconic = read_bool(f)
        read_assert_tag(f, 0x03)

    def write(self, f):
        super(Bin, self).write(f)
        write_u8(f, 0x02)

        object_count = len(self.items)
        #large bin size > max u16
        if self.large_bin or object_count > 0xffff:
            write_u8(f,  0x0f)
        else:
            write_u8(f,  0x0e)

        write_object_ref(self.root, f, self.view_setting)
        write_u64le(f, self.uid)

        #large bin size > max u16
        if self.large_bin or object_count > 0xffff:
            write_u32le(f, object_count)
        else:
            write_u16le(f, object_count)

        for bin_obj in self.items:
             write_object_ref(self.root, f, bin_obj.mob)
             write_s16le(f, bin_obj.x)
             write_s16le(f, bin_obj.y)
             write_s32le(f, bin_obj.keyframe)
             write_u8(f, bin_obj.user_placed)

        write_s32le(f, self.display_mask)
        write_s16le(f, self.display_mode)
        write_bool(f, self.sifted)

        for i in range(6):
            s = self.sifted_settings[i]
            write_s16le(f, s.method)
            write_string(f, s.string)
            write_string(f, s.column)


        write_s16le(f, len(self.sort_columns))

        for col in self.sort_columns:
            write_u8(f, col[0])
            write_string(f, col[1])

        write_s16le(f, self.mac_font)
        write_s16le(f, self.mac_font_size)
        write_s16le(f, self.mac_image_scale)

        utils.write_rect(f, self.home_rect)

        utils.write_rgb_color(f, self.background_color)
        utils.write_rgb_color(f, self.forground_color)

        write_s16le(f, self.ql_image_scale)
        write_object_ref(self.root, f, self.attributes)
        write_bool(f, self.was_iconic)
        write_u8(f, 0x03)

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
