from __future__ import (
    unicode_literals,
    absolute_import,
    print_function,
    division,
    )

from . import core
from . import utils

from . core import AVBProperty

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
    AVBProperty('name',       'name',       'string'),
    AVBProperty('kind',       'kind',       'string'),
    AVBProperty('attr_count', 'attributes', 'int16'),
    AVBProperty('attr_type',  'type',       'int16'),
    AVBProperty('attributes', 'attrList',   'reference'),
    ]
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
    AVBProperty('columns',  'Columns',  'list'),
    AVBProperty('format_descriptor', 'FormatDescriptor', 'string'),
    ]

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
                # TODO: can there be multiple?
                # not sure what this is
                num_vcid_free_columns = read_s16le(f)
                assert num_vcid_free_columns == 1
                read_assert_tag(f, 69)
                vcid_free_column_id = read_s16le(f)

                read_assert_tag(f, 71)
                fd_size = read_s32le(f)

                read_assert_tag(f, 76)
                # wrong?
                read_s32le(f)
                self.format_descriptor = f.read(fd_size).decode('utf8')
                # print(self.format_descriptor)

            else:
                raise ValueError("%s: unknown ext tag 0x%02X %d" % (str(self.class_id), tag,tag))

        read_assert_tag(f, 0x03)


class BinItem(core.AVBObject):

    propertydefs = [
    AVBProperty('ref',         'Composition',  'reference'),
    AVBProperty('x',           'Xpos',         'int16'),
    AVBProperty('y',           'Ypos',         'int16'),
    AVBProperty('keyframe',    'Keyframe',     'int32'),
    AVBProperty('user_placed', 'userPlaced',   'bool'),
    ]

    def read(self, f):
        self.object_ref = read_object_ref(self.root, f)
        self.x = read_s16le(f)
        self.y = read_s16le(f)
        self.keyframe = read_s32le(f)
        self.user_placed = read_byte(f)

    @property
    def ref(self):
        return self.object_ref.value

class SiftItem(core.AVBObject):
    propertydefs = [
    AVBProperty('method', 'SiftMethod', 'int16'),
    AVBProperty('string', 'SiftString', 'string'),
    AVBProperty('column', 'SiftColumn', 'string'),
    ]

@utils.register_class
class Bin(core.AVBObject):
    class_id = b'ABIN'
    propertydefs = [
    AVBProperty('view_setting',   'binviewsetting', 'reference'),
    AVBProperty('uid_high',         'binuid.high',    'uint32'),
    AVBProperty('uid_low',          'binuid.low',     'uint32'),
    AVBProperty('items',            'Items',          'list'), # custom
    AVBProperty('display_mask',     'DisplayMask',    'int32'),
    AVBProperty('display_mode',     'DisplayMode',    'int32'),
    AVBProperty('sifted',           'Sifted',         'bool'),
    AVBProperty('sifted_settings',  'SiftedSettring', 'list'), #custom
    AVBProperty('sort_columns',     'SortColumns',    'list'),
    AVBProperty('mac_font',         'MacFont',        'int16'),
    AVBProperty('mac_font_size',    'MacFontSize',    'int16'),
    AVBProperty('mac_image_scale',  'MacImageScale',  'int16'),
    AVBProperty('home_rect',        'HomeRect',       'rect'),
    AVBProperty('background_color', 'BackColor',      'color'),
    AVBProperty('forground_color',  'ForeColor',      'color'),
    AVBProperty('ql_image_scale',   'QLImageScale',   'int16'),
    AVBProperty('was_iconic',       'WasIconic',      'bool'),
    AVBProperty('attributes',       'BinAttr',        'reference'),
    ]

    def read(self, f):
        super(Bin, self).read(f)
        tag = read_byte(f)
        version = read_byte(f)
        assert tag == 0x02
        # print "0x%02X" % version
        assert version in (0x0e, 0x0f)

        self.view_setting_ref = read_object_ref(self.root, f)

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
        for comp in self.components:
            self.mob_dict[comp.mob_id] = comp

    @property
    def components(self):
        for item in self.items:
            yield item.ref

    def toplevel(self):
        for item in self.components:
            if  item.mob_type in ('CompositionMob', ) and item.usage_code == 0:
                yield item
