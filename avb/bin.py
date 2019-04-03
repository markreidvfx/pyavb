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
        AVBPropertyDef('attr_count', 'attributes', 'int16'),
        AVBPropertyDef('attr_type',  'type',       'int16'),
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

@utils.register_class
class BinViewSetting(Setting):
    class_id = b'BVst'
    propertydefs = Setting.propertydefs + [
        AVBPropertyDef('columns',              'Columns',          'list'),
        AVBPropertyDef('format_descriptors',   'FormatDescriptor', 'list'),
    ]
    __slots__ = ()

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


class BinItem(core.AVBObject):

    propertydefs = [
        AVBPropertyDef('mob',         'Composition',  'reference'),
        AVBPropertyDef('x',           'Xpos',         'int16'),
        AVBPropertyDef('y',           'Ypos',         'int16'),
        AVBPropertyDef('keyframe',    'Keyframe',     'int32'),
        AVBPropertyDef('user_placed', 'userPlaced',   'bool'),
    ]
    __slots__ = ()

class SiftItem(core.AVBObject):
    propertydefs = [
        AVBPropertyDef('method', 'SiftMethod', 'int16'),
        AVBPropertyDef('string', 'SiftString', 'string'),
        AVBPropertyDef('column', 'SiftColumn', 'string'),
    ]
    __slots__ = ()

@utils.register_class
class Bin(core.AVBObject):
    class_id = b'ABIN'
    propertydefs = [
        AVBPropertyDef('view_setting',   'binviewsetting', 'reference'),
        AVBPropertyDef('uid_high',         'binuid.high',    'uint32'),
        AVBPropertyDef('uid_low',          'binuid.low',     'uint32'),
        AVBPropertyDef('items',            'Items',          'list'), # custom
        AVBPropertyDef('display_mask',     'DisplayMask',    'int32'),
        AVBPropertyDef('display_mode',     'DisplayMode',    'int32'),
        AVBPropertyDef('sifted',           'Sifted',         'bool'),
        AVBPropertyDef('sifted_settings',  'SiftedSettring', 'list'), #custom
        AVBPropertyDef('sort_columns',     'SortColumns',    'list'),
        AVBPropertyDef('mac_font',         'MacFont',        'int16'),
        AVBPropertyDef('mac_font_size',    'MacFontSize',    'int16'),
        AVBPropertyDef('mac_image_scale',  'MacImageScale',  'int16'),
        AVBPropertyDef('home_rect',        'HomeRect',       'rect'),
        AVBPropertyDef('background_color', 'BackColor',      'color'),
        AVBPropertyDef('forground_color',  'ForeColor',      'color'),
        AVBPropertyDef('ql_image_scale',   'QLImageScale',   'int16'),
        AVBPropertyDef('attributes',       'BinAttr',        'reference'),
        AVBPropertyDef('was_iconic',       'WasIconic',      'bool'),
    ]
    __slots__ = ('mob_dict')

    def read(self, f):
        super(Bin, self).read(f)
        read_assert_tag(f, 0x02)

        version = read_u8(f)
        assert version in (0x0e, 0x0f)

        self.view_setting = read_object_ref(self.root, f)

        self.uid_high = read_u32le(f)
        self.uid_low  = read_u32le(f)

        # print "%04X-%04X" %(uid_high, uid_low)

        if version == 0x0e:
            object_count = read_u16le(f)
        else:
            #large bin size > max u16
            object_count = read_u32le(f)

        self.items = []

        for i in range(object_count):
            bin_obj = BinItem(self.root)
            bin_obj.mob = read_object_ref(self.root, f)
            bin_obj.x = read_s16le(f)
            bin_obj.y = read_s16le(f)
            bin_obj.keyframe = read_s32le(f)
            bin_obj.user_placed = read_u8(f)
            self.items.append(bin_obj)

        self.display_mask = read_s32le(f)
        self.display_mode = read_s16le(f)

        # sifted stuff for searching settings bin
        # don't care too much about it at the moment
        self.sifted = read_bool(f)
        self.sifted_settings= []

        for i in range(6):
            s = SiftItem(self.root)
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
        if object_count > 0xffff:
            write_u8(f,  0x0f)
        else:
            write_u8(f,  0x0e)


        write_object_ref(self.root, f, self.view_setting)

        write_u32le(f, self.uid_high)
        write_u32le(f, self.uid_low)


        #large bin size > max u16
        if object_count > 0xffff:
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

    @property
    def mobs(self):
        for item in self.items:
            yield item.mob

    def toplevel(self):
        for mob in self.mobs:
            if  mob.mob_type in ('CompositionMob', ) and mob.usage_code == 0:
                yield mob
