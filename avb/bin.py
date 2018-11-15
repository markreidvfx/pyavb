from __future__ import (
    unicode_literals,
    absolute_import,
    print_function,
    division,
    )

from . import core
from . import utils

from . utils import (
    read_byte,
    read_bool,
    read_s16le,
    read_u16le,
    read_u32le,
    read_s32le,
    read_string,
    read_object_ref,
    peek_data
)

class Setting(core.AVBObject):

    def read(self, f):
        super(Setting, self).read(f)
        tag = read_byte(f)
        version = read_byte(f)
        assert tag == 0x02
        assert version == 0x06

        self.name = read_string(f)
        self.kind = read_string(f)

        attributes = read_s16le(f)
        attr_type = read_s16le(f)
        self.attributes = read_object_ref(self.root, f)

@utils.register_class
class BinViewSetting(Setting):
    class_id = b'BVst'

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
            # print col_format, col_type, hidden

        # tag = read_byte(f)
        # assert tag == 0x03

class BinItem(object):
    def __init__(self, root):
        self.root = root
        self.object_ref = None
        self.x = None
        self.y = None
        self.keyframe = None
        self.user_placed = None

    def read(self, f):
        self.object_ref = read_object_ref(self.root, f)
        self.x = read_s16le(f)
        self.y = read_s16le(f)
        self.keyframe = read_s32le(f)
        self.user_placed = read_byte(f)

    @property
    def ref(self):
        return self.object_ref.value

@utils.register_class
class Bin(core.AVBObject):
    class_id = b'ABIN'

    def read(self, f):
        super(Bin, self).read(f)
        tag = read_byte(f)
        version = read_byte(f)
        assert tag == 0x02
        # print "0x%02X" % version
        assert version in (0x0e, 0x0f)

        self.view_setting_ref = read_object_ref(self.root, f)

        uid_high = read_u32le(f)
        uid_low  = read_u32le(f)

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
        self.sifted = read_byte(f)
        self.sifted_settings= []

        for i in range(6):
            sift_method = read_s16le(f)
            sift_str = read_string(f)
            sift_column = read_string(f)
            d= [sift_method, sift_str,sift_column]
            self.sifted_settings.append(d)

        # a bit messy here
        b = read_byte(f)
        if b:
            sift_str = read_string(f)
            sift_column = read_string(f)
            d = [sift_method, sift_str, sift_column]
            self.sifted_settings.append(d)
            self.sort_column_count = read_s16le(f)
            assert b == 1
            f.read(4)
        else:
            f.seek(f.tell()-1)
            self.sort_column_count = read_s16le(f)
            f.read(6)


        self.home_rect = utils.read_rect(f)
        self.background_color = utils.read_rgb_color(f)
        self.forground_color = utils.read_rgb_color(f)

        self.ql_image_scale = read_s16le(f)

        self.attributes = read_object_ref(self.root, f)
        # print(self.attributes)

    @property
    def components(self):
        for item in self.items:
            yield item.ref

    def toplevel(self):
        for item in self.components:
            if  item.mob_type in ('CompositionMob', ) and item.usage_code == 0:
                yield item
