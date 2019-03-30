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
    read_byte,
    read_bool,
    read_s16le,
    read_u16le,
    read_u32le,
    read_s32le,
    read_string,
    read_assert_tag,
    read_object_ref,
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
        tag = read_byte(f)
        version = read_byte(f)
        assert tag == 0x02
        assert version == 0x06

        self.name = read_string(f)
        self.kind = read_string(f)

        self.attr_count = read_s16le(f)
        self.attr_type = read_s16le(f)
        self.attributes = read_object_ref(self.root, f)

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
        tag = read_byte(f)
        version = read_byte(f)
        assert tag == 0x02
        assert version == 10

        self.columns = []

        column_count = read_u16le(f)
        for i in range(column_count):
            d = {}
            d['title'] = read_string(f)
            d['format'] = read_s16le(f)
            d['type'] = read_s16le(f)
            d['hidden'] = read_bool(f)
            # print d
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


class BinItem(core.AVBObject):

    propertydefs = [
        AVBPropertyDef('mob',         'Composition',  'reference'),
        AVBPropertyDef('x',           'Xpos',         'int16'),
        AVBPropertyDef('y',           'Ypos',         'int16'),
        AVBPropertyDef('keyframe',    'Keyframe',     'int32'),
        AVBPropertyDef('user_placed', 'userPlaced',   'bool'),
    ]
    __slots__ = ()

    def read(self, f):
        self.mob = read_object_ref(self.root, f)
        self.x = read_s16le(f)
        self.y = read_s16le(f)
        self.keyframe = read_s32le(f)
        self.user_placed = read_byte(f)

    # @property
    # def ref(self):
    #     return self.object_ref.value

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
        AVBPropertyDef('was_iconic',       'WasIconic',      'bool'),
        AVBPropertyDef('attributes',       'BinAttr',        'reference'),
    ]
    __slots__ = ('mob_dict')

    def read(self, f):
        super(Bin, self).read(f)
        tag = read_byte(f)
        version = read_byte(f)
        assert tag == 0x02
        # print "0x%02X" % version
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
            bin_obj.read(f)
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
            direction = read_byte(f)
            col = read_string(f)
            self.sort_columns.append([direction, col])


        self.mac_font = read_s16le(f)
        self.mac_font_size = read_s16le(f)
        self.mac_image_scale = read_s16le(f)

        self.home_rect = utils.read_rect(f)

        self.background_color = utils.read_rgb_color(f)
        self.forground_color = utils.read_rgb_color(f)

        self.ql_image_scale = read_s16le(f)
        self.was_iconic = read_bool(f)

        self.attributes = read_object_ref(self.root, f)
        read_assert_tag(f, 0x03)

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
