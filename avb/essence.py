from __future__ import (
    unicode_literals,
    absolute_import,
    print_function,
    division,
    )

from io import BytesIO

from . import core
from . import utils


from . utils import (
    read_byte,
    read_bool,
    read_s8,
    read_s16le,
    read_u16le,
    read_u32le,
    read_s32le,
    read_s64le,
    read_string,
    read_raw_uuid,
    reverse_str,
    read_exp10_encoded_float,
    read_object_ref,
    read_datetime,
    peek_data
)

@utils.register_class
class FileLocator(core.AVBObject):
    class_id = 'FILE'

    def read(self, f):
        super(FileLocator, self).read(f)

        tag = read_byte(f)
        version = read_byte(f)

        assert tag == 0x02
        assert version == 2

        self.path = read_string(f)

        if self.path:
            tag = read_byte(f)
            version = read_byte(f)
            assert tag == 0x01
            assert version == 1
            tag = read_byte(f)
            assert tag == 76
            self.posix_path1 = read_string(f)

            tag = read_byte(f)
            version = read_byte(f)

            assert tag == 0x01
            assert version == 2
            tag = read_byte(f)
            assert tag == 76
            self.posix_path2 = read_string(f)
        else:
            self.posix_path1 = None
            self.posix_path2 = None

        # end tag
        tag = read_byte(f)
        assert tag == 0x03

@utils.register_class
class MediaDescriptor(core.AVBObject):
    class_id = 'MDES'

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

        # print()
        # print(peek_data(f).encode('hex'))
        # print()

        tag = read_byte(f)
        self.uuid = None

        if tag == 0x01:

            version = read_byte(f)

            if version == 3:
                tag = read_byte(f)
                assert tag == 72
                # TODO: look into this, pixel_layout attribute?
                self.pixel_layout = read_object_ref(self.root, f)
            else:
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
class PCMADescriptor(MediaFileDescriptor):
    class_id = 'PCMA'

    def read(self, f):
        super(PCMADescriptor, self).read(f)
        print(peek_data(f).encode('hex'))

        tag = read_byte(f)
        version = read_byte(f)

        assert tag == 0x02
        assert version == 0x01

        something = read_u16le(f)
        self.quantization_bits = read_u16le(f)
        self.sample_rate = read_u32le(f)
        something = read_u16le(f)
        something = read_byte(f)
        self.audio_ref_level = read_s8(f)
        something = read_byte(f)

        self.block_align = read_u32le(f)
        self.dial_norm = read_u16le(f)

        something = read_u32le(f)
        something = read_u32le(f)

        something = read_u16le(f)

        self.average_bps = read_u32le(f)

        # read_object_ref(self.root, f)

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

        self.check_ext_header(f, 0x01, 69)
        self.frame_index_byte_order = read_s16le(f)

        self.check_ext_header(f, 0x02, 71)
        self.frame_sample_size = read_s32le(f)

        self.check_ext_header(f, 0x03, 71)
        self.first_frame_offset = read_s32le(f)

        self.check_ext_header(f, 0x04, 71)
        self.client_fill_start = read_s32le(f)

        version = read_byte(f)
        assert version == 71
        self.client_fill_end = read_s32le(f)

        self.check_ext_header(f, 0x05, 71)
        self.offset_to_rle_frame_index = read_s32le(f)

        # print(peek_data(f).encode('hex'))
        # self.check_ext_header(f, 8, 71)
        tag = read_byte(f)
        if tag != 0x01:
            raise ValueError()


        tag = read_byte(f)
        if tag == 15:
            read_u16le(f)
            return
        assert tag == 8

        # valid
        self.check_version_tag(f, 71)
        x = read_s32le(f)
        self.check_version_tag(f, 71)
        y = read_s32le(f)
        self.valid_x = [x, y]

        self.check_version_tag(f, 71)
        x = read_s32le(f)
        self.check_version_tag(f, 71)
        y = read_s32le(f)
        self.valid_y = [x, y]

        self.check_version_tag(f, 71)
        x = read_s32le(f)
        self.check_version_tag(f, 71)
        y = read_s32le(f)
        self.valid_width = [x, y]

        self.check_version_tag(f, 71)
        x = read_s32le(f)
        self.check_version_tag(f, 71)
        y = read_s32le(f)
        self.valid_height = [x, y]

        # print(self.valid_x, self.valid_y)
        # print(self.valid_width, self.valid_height)

        # essence
        self.check_version_tag(f, 71)
        x = read_s32le(f)
        self.check_version_tag(f, 71)
        y = read_s32le(f)
        self.essence_x = [x, y]

        self.check_version_tag(f, 71)
        x = read_s32le(f)
        self.check_version_tag(f, 71)
        y = read_s32le(f)
        self.essence_y = [x, y]

        self.check_version_tag(f, 71)
        x = read_s32le(f)
        self.check_version_tag(f, 71)
        y = read_s32le(f)
        self.essence_width = [x, y]

        self.check_version_tag(f, 71)
        x = read_s32le(f)
        self.check_version_tag(f, 71)
        y = read_s32le(f)
        self.essence_height = [x, y]

        # source
        self.check_version_tag(f, 71)
        x = read_s32le(f)
        self.check_version_tag(f, 71)
        y = read_s32le(f)
        self.source_x = [x, y]

        self.check_version_tag(f, 71)
        x = read_s32le(f)
        self.check_version_tag(f, 71)
        y = read_s32le(f)
        self.source_y = [x, y]

        self.check_version_tag(f, 71)
        x = read_s32le(f)
        self.check_version_tag(f, 71)
        y = read_s32le(f)
        self.source_width = [x, y]

        self.check_version_tag(f, 71)
        x = read_s32le(f)
        self.check_version_tag(f, 71)
        y = read_s32le(f)
        self.souce_height = [x, y]
        # self.check_ext_header(f, 0x0B, 80)

        tag = read_byte(f)
        assert tag == 0x01
        version = read_byte(f)

        if version == 11:
            f.read(38)
        elif version == 15:
            something = read_u16le(f)
        else:
            raise ValueError()


    def check_version_tag(self, f, version):
        version_mark = read_byte(f)
        assert version_mark == version

    def check_ext_header(self, f, tag_mark, version_mark):
        tag = read_byte(f)
        assert tag == 0x01
        tag = read_byte(f)
        assert tag == tag_mark
        version = read_byte(f)
        assert version == version_mark


@utils.register_class
class CDCIDescriptor(DIDDescriptor):
    class_id = 'CDCI'

    def read(self, f):
        super(CDCIDescriptor, self).read(f)
        tag = read_byte(f)
        version = read_byte(f)

        assert tag == 0x02
        assert version == 0x02

        self.horizontal_subsampling = read_u32le(f)
        self.vertical_subsampling = read_u32le(f)
        self.component_width = read_u32le(f)

        self.color_sitting = read_s16le(f)
        self.black_ref_level = read_u32le(f)
        self.white_ref_level = read_u32le(f)
        self.color_range = read_u32le(f)

        self.offset_to_frames64 = read_s64le(f)

        tag = read_byte(f)
        if tag == 0x03:
            return

        assert tag == 0x01
        tag = read_byte(f)
        assert tag == 0x01

        version = read_byte(f)
        assert version == 72

        something1 = read_u32le(f)

        tag = read_byte(f)
        assert tag == 0x01
        tag = read_byte(f)
        assert tag == 0x02
        version = read_byte(f)
        assert version == 72

        something2 = read_u32le(f)

        tag = read_byte(f)
        assert tag == 0x03


def decode_pixel_layout(pixel_layout, pixel_struct):

    layout = []
    for i in range(8):
        code = read_byte(pixel_layout)
        depth = read_byte(pixel_struct)
        if not code:
            break
        layout.append({'Code':code, 'Size':depth})

    return layout

@utils.register_class
class RGBADescriptor(DIDDescriptor):
    class_id = 'RGBA'

    def read(self, f):
        super(RGBADescriptor, self).read(f)

        tag = read_byte(f)
        version = read_byte(f)

        assert tag == 0x02
        assert version == 0x01

        # this seems to be encode the same way as in AAF
        layout_size = read_u32le(f)
        pixel_layout = BytesIO(f.read(layout_size))

        struct_size =  read_u32le(f)
        pixel_struct = BytesIO(f.read(struct_size))

        self.pixel_layout = decode_pixel_layout(pixel_layout, pixel_struct)

        # print([self.pixel_struct])

        palette_layout_size = read_u32le(f)
        assert palette_layout_size == 0

        palette_struct_size = read_u32le(f)
        assert palette_struct_size == 0

        palette_size = read_u32le(f)
        assert palette_size == 0

        # print(self)
        # print('!!', peek_data(f).encode('hex'))

        tag = read_byte(f)

        if tag == 0x03:
            return
        elif tag == 0x01:
            tag = read_byte(f)
            assert tag == 0x03
            version = read_byte(f)
            assert version == 72
            something = read_u32le(f)
            version = read_byte(f)
            assert version == 72
            something = read_u32le(f)

        tag = read_byte(f)
        assert tag == 0x03
