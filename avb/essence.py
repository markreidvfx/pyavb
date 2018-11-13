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
    read_raw_uuid,
    reverse_str,
    read_exp10_encoded_float,
    read_object_ref,
    read_datetime,
    peek_data
)

class MediaDescriptor(core.AVBObject):
    def read(self, f):
        super(MediaDescriptor, self).read(f)
        tag = read_byte(f)
        version = read_byte(f)

        assert tag == 0x02
        assert version == 0x03

        mob_kind = read_byte(f)
        self.locator = read_object_ref(self.root, f)
        self.intermediate = read_bool(f)
        self.physical_media = read_object_ref(self.root, f)

        # print peek_data(f).encode('hex')

        tag = read_byte(f)

        if tag == 0x01:

            version = read_byte(f)

            assert tag == 0x01
            assert version == 0x01
            tag = read_byte(f)
            assert tag == 65

            uuid_len = read_s32le(f)
            assert uuid_len == 16

            self.uuid = read_raw_uuid(f)
        else:
            f.seek(f.tell()-1)


class MediaFileDescriptor(MediaDescriptor):
    class_id = 'MDFL'

    def read(self, f):
        super(MediaFileDescriptor, self).read(f)

        tag = read_byte(f)

        # print peek_data(f).encode('hex')
        version = read_byte(f)
        assert tag == 0x02
        assert version == 0x03

        self.edit_rate = read_exp10_encoded_float(f)
        self.length = read_u32le(f)
        self.is_omfi = read_s16le(f)
        self.data_offset = read_u32le(f)

@utils.register_class
class DIDDescriptor(MediaFileDescriptor):
    class_id = 'DIDD'

    def read(self, f):
        super(DIDDescriptor, self).read(f)
        tag = read_byte(f)
        version = read_byte(f)

        assert tag == 0x02
        assert version == 0x02

        self.stored_height = read_s32le(f)
        self.stored_width  = read_s32le(f)

        self.sampled_height = read_s32le(f)
        self.sampled_width  = read_s32le(f)

        self.sampled_x_offset = read_s32le(f)
        self.sampled_y_offset = read_s32le(f)

        self.display_height = read_s32le(f)
        self.display_width  = read_s32le(f)

        self.display_x_offset = read_s32le(f)
        self.display_y_offset = read_s32le(f)

        self.frame_layout = read_s16le(f)

        numerator = read_s32le(f)
        denominator = read_s32le(f)
        self.aspect_ratio = [numerator, denominator]

        line_map_byte_size = read_s32le(f)
        self.line_map = []
        if line_map_byte_size:
            for i in range(line_map_byte_size // 4):
                v = read_s32le(f)
                self.line_map.append(v)

        self.alpha_transparency = read_s32le(f)
        self.uniformness = read_bool(f)

        self.did_image_size = read_s32le(f)

        self.next_did_desc = read_object_ref(self.root, f)

        self.compress_method = reverse_str(f.read(4))

        self.resolution_id = read_s32le(f)
        self.image_alignment_factor =  read_s32le(f)

@utils.register_class
class CDCIDescriptor(DIDDescriptor):
    class_id = 'CDCI'

#@utils.register_class
class RGBADescriptor(DIDDescriptor):
    class_id = 'RGBA'
