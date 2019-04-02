from __future__ import (
    unicode_literals,
    absolute_import,
    print_function,
    division,
    )

from io import BytesIO

from . import core
from . import utils
from .core import AVBPropertyDef, AVBRefList

from . utils import (
    read_u8,     write_u8,
    read_bool,   write_bool,
    read_s8,
    read_s16le,
    read_u16le,
    read_u32le,
    read_s32le,
    read_s64le,
    read_u64le,
    read_string,
    read_raw_uuid, write_raw_uuid,
    read_uuid,
    reverse_str,
    read_exp10_encoded_float,
    read_object_ref, write_object_ref,
    read_datetime,
    iter_ext,
    read_assert_tag,
    peek_data
)

@utils.register_class
class MediaDescriptor(core.AVBObject):
    class_id = b'MDES'
    propertydefs = [
        AVBPropertyDef('mob_kind',       'OMFI:MDES:MobKind',         'int8'),
        AVBPropertyDef('locator',        'OMFI:MDES:Locator',         'reference'),
        AVBPropertyDef('intermediate',   'OMFI:MDES:MC:Intermediate', 'bool'),
        AVBPropertyDef('physical_media', 'OMFI:MOBJ:PhysicalMedia',   'reference'),
        AVBPropertyDef('uuid',           'OMFI:AMDL:acfUID',          'UUID'),
        AVBPropertyDef('attributes',     'OMFI:AMDL:Attributes',      'reference'),
    ]
    __slots__ = ()

    def read(self, f):
        super(MediaDescriptor, self).read(f)
        read_assert_tag(f, 0x02)
        read_assert_tag(f, 0x03)

        self.mob_kind = read_u8(f)
        self.locator = []
        self.locator = read_object_ref(self.root, f)
        self.intermediate = read_bool(f)
        self.physical_media = read_object_ref(self.root, f)

        # print('sss', self.locator)
        # print(peek_data(f).encode('hex'))

        for tag in iter_ext(f):

            if tag == 0x01:
                read_assert_tag(f, 65)
                uuid_len = read_s32le(f)
                assert uuid_len == 16
                self.uuid = read_raw_uuid(f)
            elif tag == 0x03:
                read_assert_tag(f, 72)
                self.attributes = read_object_ref(self.root, f)
            else:
                raise ValueError("%s: unknown ext tag 0x%02X %d" % (str(self.class_id), tag,tag))

        if self.class_id == b'MDES':
            read_assert_tag(f, 0x03)

    def write(self, f):
        super(MediaDescriptor, self).write(f)
        write_u8(f, 0x02)
        write_u8(f, 0x03)

        write_u8(f, self.mob_kind)
        write_object_ref(self.root, f, self.locator)
        write_bool(f, self.intermediate)
        write_object_ref(self.root, f, self.physical_media)

        if hasattr(self, 'uuid'):
            write_u8(f, 0x01)
            write_u8(f, 0x01)
            write_u8(f, 65)
            write_raw_uuid(f, self.uuid)

        if hasattr(self, 'attributes'):
            write_u8(f, 0x01)
            write_u8(f, 0x03)
            write_u8(f, 72)
            write_object_ref(self.root, f, self.attributes)

        if self.class_id == b'MDES':
            write_u8(f, 0x03)


@utils.register_class
class TapeDescriptor(MediaDescriptor):
    class_id = b'MDTP'
    propertydefs = MediaDescriptor.propertydefs + [
        AVBPropertyDef('cframe', 'OMFI:MDTP:CFrame', "int16")
    ]
    __slots__ = ()

    def read(self, f):
        super(TapeDescriptor, self).read(f)
        read_assert_tag(f, 0x02)
        read_assert_tag(f, 0x02)

        self.cframe = read_s16le(f)
        read_assert_tag(f, 0x03)

class MediaFileDescriptor(MediaDescriptor):
    class_id = b'MDFL'
    propertydefs = MediaDescriptor.propertydefs + [
        AVBPropertyDef('edit_rate', 'EdRate', "fexp10"),
        AVBPropertyDef('length', 'OMFI:MDFL:Length', 'int32'),
        AVBPropertyDef('is_omfi', 'OMFI:MDFL:IsOMFI', 'int16'),
        AVBPropertyDef('data_offset', 'OMFI:MDFL:dataOffset', 'int32'),
    ]
    __slots__ = ()

    def read(self, f):
        super(MediaFileDescriptor, self).read(f)
        read_assert_tag(f, 0x02)
        read_assert_tag(f, 0x03)

        self.edit_rate = read_exp10_encoded_float(f)
        self.length = read_s32le(f)
        self.is_omfi = read_s16le(f)
        self.data_offset = read_s32le(f)


@utils.register_class
class MultiDescriptor(MediaFileDescriptor):
    class_id = b'MULD'
    propertydefs = MediaFileDescriptor.propertydefs + [
        AVBPropertyDef('descriptors', 'OMFI:MULD:Descriptors', "ref_list"),
    ]
    __slots__ = ()

    def read(self, f):
        super(MultiDescriptor, self).read(f)
        read_assert_tag(f, 0x02)
        read_assert_tag(f, 0x01)

        count = read_s32le(f)
        self.descriptors = AVBRefList(self.root)
        for i in range(count):
            ref = read_object_ref(self.root, f)
            self.descriptors.append(ref)

        read_assert_tag(f, 0x03)

@utils.register_class
class PCMADescriptor(MediaFileDescriptor):
    class_id = b'PCMA'
    propertydefs = MediaFileDescriptor.propertydefs + [
        AVBPropertyDef('channels',                    'OMFI:MDAU:NumChannels',               'uint16'),
        AVBPropertyDef('quantization_bits',           'OMFI:MDAU:BitsPerSample',             'uint16'),
        AVBPropertyDef('sample_rate',                 'EdRate',                              'fexp10'),
        AVBPropertyDef('locked',                      'OMFI:PCMA:Locked',                    'bool'),
        AVBPropertyDef('audio_ref_level',             'OMFI:PCMA:AudioRefLevel',             'int16'),
        AVBPropertyDef('electro_spatial_formulation', 'OMFI:PCMA:ElectroSpatialFormulation', 'int32'),
        AVBPropertyDef('dial_norm',                   'OMFI:PCMA:DialNorm',                  'uint16'),
        AVBPropertyDef('coding_format',               'OMFI:PCMA:AudioCodingFormat',         'int32'),
        AVBPropertyDef('block_align',                 'OMFI:PCMA:BlockAlignment',            'int32'),
        AVBPropertyDef('sequence_offset',             'OMFI:PCMA:SequenceOffset',            'uint16'),
        AVBPropertyDef('average_bps',                 'OMFI:PCMA:AverageBytesPerSecond',     'int32'),
        AVBPropertyDef('has_peak_envelope_data',      'OMFI:PCMA:HasPeakEnvelopeData',       'bool'),
        AVBPropertyDef('peak_envelope_version',       'OMFI:PCMA:PeakEnvelopeVersion',       'int32'),
        AVBPropertyDef('peak_envelope_format',        'OMFI:PCMA:PeakEnvelopeFormat',        'int32'),
        AVBPropertyDef('points_per_peak_value',       'OMFI:PCMA:PointsPerPeakValue',        'int32'),
        AVBPropertyDef('peak_envelope_block_size',    'OMFI:PCMA:PeakEnvelopeBlockSize',     'int32'),
        AVBPropertyDef('peak_channel_count',          'OMFI:PCMA:PeakChannelCount',          'int32'),
        AVBPropertyDef('peak_frame_count',            'OMFI:PCMA:PeakFrameCount',            'int32'),
        AVBPropertyDef('peak_of_peaks_offset',        'OMFI:PCMA:PeakOfPeaksOffset',         'uint64'),
        AVBPropertyDef('peak_envelope_timestamp',     'OMFI:PCMA:PeakEnvelopeTimestamp',     'int32'),
    ]
    __slots__ = ()

    def read(self, f):
        super(PCMADescriptor, self).read(f)
        read_assert_tag(f, 0x02)
        read_assert_tag(f, 0x01)

        self.channels = read_u16le(f)
        self.quantization_bits = read_u16le(f)
        self.sample_rate = read_exp10_encoded_float(f)

        self.locked = read_bool(f)
        self.audio_ref_level = read_s16le(f)
        self.electro_spatial_formulation = read_s32le(f)
        self.dial_norm = read_u16le(f)

        self.coding_format = read_u32le(f)
        self.block_align = read_u32le(f)

        self.sequence_offset = read_u16le(f)
        self.average_bps = read_u32le(f)
        self.has_peak_envelope_data = read_bool(f)

        self.peak_envelope_version = read_s32le(f)
        self.peak_envelope_format = read_s32le(f)
        self.points_per_peak_value = read_s32le(f)
        self.peak_envelope_block_size = read_s32le(f)
        self.peak_channel_count = read_s32le(f)
        self.peak_frame_count = read_s32le(f)
        self.peak_of_peaks_offset = read_u64le(f)
        self.peak_envelope_timestamp = read_s32le(f)

        read_assert_tag(f, 0x03)

@utils.register_class
class DIDDescriptor(MediaFileDescriptor):
    class_id = b'DIDD'
    propertydefs = MediaFileDescriptor.propertydefs + [
        AVBPropertyDef('stored_height',              'OMFI:DIDD:StoredHeight',                            'int32'),
        AVBPropertyDef('stored_width',               'OMFI:DIDD:StoredWidth',                             'int32'),
        AVBPropertyDef('sampled_height',             'OMFI:DIDD:SampledHeight',                           'int32'),
        AVBPropertyDef('sampled_width',              'OMFI:DIDD:SampledWidth',                            'int32'),
        AVBPropertyDef('sampled_x_offset',           'OMFI:DIDD:SampledXOffset',                          'int32'),
        AVBPropertyDef('sampled_y_offset',           'OMFI:DIDD:SampledYOffset',                          'int32'),
        AVBPropertyDef('display_height',             'OMFI:DIDD:DisplayHeight',                           'int32'),
        AVBPropertyDef('display_width',              'OMFI:DIDD:DisplayWidth',                            'int32'),
        AVBPropertyDef('display_x_offset',           'OMFI:DIDD:DisplayXOffset',                          'int32'),
        AVBPropertyDef('display_y_offset',           'OMFI:DIDD:DisplayYOffset',                          'int32'),
        AVBPropertyDef('frame_layout',               'OMFI:DIDD:FrameLayout',                             'int16'),
        AVBPropertyDef('aspect_ratio',               'OMFI:DIDD:ImageAspectRatio',                        'rational'),
        AVBPropertyDef('line_map',                   'OMFI:DIDD:VideoLineMap',                            'list'),
        AVBPropertyDef('alpha_transparency',         'OMFI:DIDD:AlphaTransparency',                       'int32'),
        AVBPropertyDef('uniformness',                'OMFI:DIDD:Uniformness',                             'bool'),
        AVBPropertyDef('did_image_size',             'OMFI:DIDD:DIDImageSize',                            'int32'),
        AVBPropertyDef('next_did_desc',              "OMFI:DIDD:NextDIDDesc",                         'reference'),
        AVBPropertyDef('compress_method',            'OMFI:DIDD:DIDCompressMethod',                       'bytes'),
        AVBPropertyDef('resolution_id',              'OMFI:DIDD:DIDResolutionID',                         'int32'),
        AVBPropertyDef('image_alignment_factor',     'OMFI:DIDD:ImageAlignmentFactor',                    'int32'),
        AVBPropertyDef('frame_index_byte_order',     'OMFI:DIDD:FrameIndexByteOrder',                     'int16'),
        AVBPropertyDef('frame_sample_size',          'OMFI:DIDD:FrameSampleSize',                         'int32'),
        AVBPropertyDef('first_frame_offset',         'OMFI:DIDD:FirstFrameOffset',                        'int32'),
        AVBPropertyDef('client_fill_start',          'OMFI:DIDD:ClientFillStart',                         'int32'),
        AVBPropertyDef('client_fill_end',            'OMFI:DIDD:ClientFillEnd',                           'int32'),
        AVBPropertyDef('offset_to_rle_frame_index',  'OMFI:DIDD:OffsetToRLEFrameIndexes',                 'int32'),
        AVBPropertyDef('valid_box',                  'OMFI:DIDD:Valid',                                   'bounds_box'),
        AVBPropertyDef('essence_box',                'OMFI:DIDD:Essence',                                 'bounds_box'),
        AVBPropertyDef('source_box',                 'OMFI:DIDD:Source',                                  'bounds_box'),
        AVBPropertyDef('framing_box',                'OMFI:DIDD:Framing',                                 'bounds_box'),
        AVBPropertyDef('reformatting_option',        'OMFI:DIDD:ReformattingOption',                      'int32'),
        AVBPropertyDef('transfer_characteristic',    'OMFI:DIDD:TransferCharacteristic',                  'UUID'),
        AVBPropertyDef('color_primaries',            'OMFI:DIDD:ColorPrimaries',                          'UUID'),
        AVBPropertyDef('coding_equations',           'OMFI:DIDD:CodingEquations',                         'UUID'),
        AVBPropertyDef('frame_checked_with_mapper',  'OMFI:DIDD:FrameSampleSizeHasBeenCheckedWithMapper', 'bool'),
    ]
    __slots__ = ()

    def read(self, f):
        super(DIDDescriptor, self).read(f)
        read_assert_tag(f, 0x02)
        read_assert_tag(f, 0x02)

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

        for tag in iter_ext(f):
            if tag == 0x01:
                read_assert_tag(f, 69)
                self.frame_index_byte_order = read_s16le(f)

            elif tag == 0x02:
                read_assert_tag(f, 71)
                self.frame_sample_size = read_s32le(f)

            elif tag == 0x03:
                read_assert_tag(f, 71)
                self.first_frame_offset = read_s32le(f)

            elif tag == 0x04:
                read_assert_tag(f, 71)
                self.client_fill_start = read_s32le(f)

                read_assert_tag(f, 71)
                self.client_fill_end = read_s32le(f)

            elif tag == 0x05:
                read_assert_tag(f, 71)
                self.offset_to_rle_frame_index = read_s32le(f)

            elif tag == 0x08:
                # valid
                self.valid_box = []
                read_assert_tag(f, 71)
                x = read_s32le(f)
                read_assert_tag(f, 71)
                y = read_s32le(f)
                self.valid_box.append([x, y])

                read_assert_tag(f, 71)
                x = read_s32le(f)
                read_assert_tag(f, 71)
                y = read_s32le(f)
                self.valid_box.append([x, y])

                read_assert_tag(f, 71)
                x = read_s32le(f)
                read_assert_tag(f, 71)
                y = read_s32le(f)
                self.valid_box.append([x, y])

                read_assert_tag(f, 71)
                x = read_s32le(f)
                read_assert_tag(f, 71)
                y = read_s32le(f)
                self.valid_box.append([x, y])

                # essence
                self.essence_box = []
                read_assert_tag(f, 71)
                x = read_s32le(f)
                read_assert_tag(f, 71)
                y = read_s32le(f)
                self.essence_box.append([x, y])

                read_assert_tag(f, 71)
                x = read_s32le(f)
                read_assert_tag(f, 71)
                y = read_s32le(f)
                self.essence_box.append([x, y])

                read_assert_tag(f, 71)
                x = read_s32le(f)
                read_assert_tag(f, 71)
                y = read_s32le(f)
                self.essence_box.append([x, y])

                read_assert_tag(f, 71)
                x = read_s32le(f)
                read_assert_tag(f, 71)
                y = read_s32le(f)
                self.essence_box.append([x, y])

                # source
                self.source_box = []
                read_assert_tag(f, 71)
                x = read_s32le(f)
                read_assert_tag(f, 71)
                y = read_s32le(f)
                self.source_box.append([x, y])

                read_assert_tag(f, 71)
                x = read_s32le(f)
                read_assert_tag(f, 71)
                y = read_s32le(f)
                self.source_box.append([x, y])

                read_assert_tag(f, 71)
                x = read_s32le(f)
                read_assert_tag(f, 71)
                y = read_s32le(f)
                self.source_box.append([x, y])

                read_assert_tag(f, 71)
                x = read_s32le(f)
                read_assert_tag(f, 71)
                y = read_s32le(f)
                self.source_box.append([x, y])

            elif tag == 9:
                # print("\n??!", peek_data(f).encode('hex'), '\n')
                self.framing_box = []
                read_assert_tag(f, 71)
                x = read_s32le(f)
                read_assert_tag(f, 71)
                y = read_s32le(f)
                self.framing_box.append([x, y])

                read_assert_tag(f, 71)
                x = read_s32le(f)
                read_assert_tag(f, 71)
                y = read_s32le(f)
                self.framing_box.append([x, y])

                read_assert_tag(f, 71)
                x = read_s32le(f)
                read_assert_tag(f, 71)
                y = read_s32le(f)
                self.framing_box.append([x, y])

                read_assert_tag(f, 71)
                x = read_s32le(f)
                read_assert_tag(f, 71)
                y = read_s32le(f)
                self.framing_box.append([x, y])

                read_assert_tag(f, 71)
                self.reformatting_option = read_s32le(f)

            elif tag == 10:
                read_assert_tag(f, 80)
                self.transfer_characteristic = read_raw_uuid(f)
            elif tag == 11:
                read_assert_tag(f, 80)
                self.color_primaries =  read_raw_uuid(f)
                read_assert_tag(f, 80)
                self.coding_equations = read_raw_uuid(f)

            elif tag == 15:
                read_assert_tag(f, 66)
                self.frame_checked_with_mapper = read_bool(f)

            else:
                raise ValueError("%s: unknown ext tag 0x%02X %d" % (str(self.class_id), tag,tag))

        if self.class_id == b'DIDD':
            read_assert_tag(f, 0x03)

@utils.register_class
class CDCIDescriptor(DIDDescriptor):
    class_id = b'CDCI'
    propertydefs = DIDDescriptor.propertydefs + [
        AVBPropertyDef('horizontal_subsampling', 'OMFI:CDCI:HorizontalSubsampling',         'uint32'),
        AVBPropertyDef('vertical_subsampling',   'OMFI:CDCI:VerticalSubsampling',           'uint32'),
        AVBPropertyDef('component_width',        'OMFI:CDCI:ComponentWidth',                'int32'),
        AVBPropertyDef('color_sitting',          'OMFI:CDCI:ColorSiting',                   'int16'),
        AVBPropertyDef('black_ref_level',        'OMFI:CDCI:BlackReferenceLevel',           'uint32'),
        AVBPropertyDef('white_ref_level',        'OMFI:CDCI:WhiteReferenceLevel',           'uint32'),
        AVBPropertyDef('color_range',            'OMFI:CDCI:ColorRange',                    'uint32'),
        AVBPropertyDef('frame_index_offset',     'OMFI:JPED:OffsetToFrameIndexes',          'uint64'),
        AVBPropertyDef('alpha_sampled_width',    'OMFI:CDCI:AlphaSamledWidth',              'uint32'),
        AVBPropertyDef('ignore_bw',              'OMFI:CDCI:IgnoreBWRefLevelAndColorRange', 'uint32'),
    ]
    __slots__ = ()

    def read(self, f):
        super(CDCIDescriptor, self).read(f)
        read_assert_tag(f, 0x02)
        read_assert_tag(f, 0x02)

        self.horizontal_subsampling = read_u32le(f)
        self.vertical_subsampling = read_u32le(f)
        self.component_width = read_s32le(f)

        self.color_sitting = read_s16le(f)
        self.black_ref_level = read_u32le(f)
        self.white_ref_level = read_u32le(f)
        self.color_range = read_u32le(f)

        self.frame_index_offset = read_s64le(f)

        for tag in iter_ext(f):
            if tag == 0x01:
                read_assert_tag(f, 72)
                self.alpha_sampled_width = read_u32le(f)

            elif tag == 0x02:
                read_assert_tag(f, 72)
                self.ignore_bw = read_u32le(f)
            else:
                raise ValueError("%s: unknown ext tag 0x%02X %d" % (str(self.class_id), tag,tag))

        read_assert_tag(f, 0x03)

def decode_pixel_layout(pixel_layout, pixel_struct):

    layout = []
    for i in range(8):
        code = read_u8(pixel_layout)
        depth = read_u8(pixel_struct)
        if not code:
            break
        layout.append({'Code':code, 'Size':depth})

    return layout

@utils.register_class
class RGBADescriptor(DIDDescriptor):
    class_id = b'RGBA'
    propertydefs = DIDDescriptor.propertydefs + [
        AVBPropertyDef('pixel_layout',       'OMFI:RGBA:PixelLayout',          'list'),
        AVBPropertyDef('palette',            'OMFI:RGBA:Palette',              'list'),
        AVBPropertyDef('frame_index_offset', 'OMFI:RGBA:OffsetToFrameIndexes', 'uint64'),
        AVBPropertyDef('has_comp_min_ref',   'OMFI:RGBA:HasCompMinRef',        'bool'),
        AVBPropertyDef('comp_min_ref',       'OMFI:RGBA:ComponentMinRef',      'uint32'),
        AVBPropertyDef('has_comp_max_ref',   'OMFI:RGBA:HasCompMaxRef',        'bool'),
        AVBPropertyDef('comp_max_ref',       'OMFI:RGBA:ComponentMaxRef',      'uint32'),
        AVBPropertyDef('alpha_min_ref',      'OMFI:RGBA:AlphaMinRef',          'uint32'),
        AVBPropertyDef('alpha_max_ref',      'OMFI:RGBA:AlphaMaxRef',          'uint32'),
    ]
    __slots__ = ()

    def read(self, f):
        super(RGBADescriptor, self).read(f)
        read_assert_tag(f, 0x02)
        read_assert_tag(f, 0x01)

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

        for tag in iter_ext(f):
            if tag == 0x01:
                read_assert_tag(f, 77)
                self.frame_index_offset = read_u64le(f)

            elif tag == 0x02:
                read_assert_tag(f, 66)
                self.has_comp_min_ref = read_bool(f)

                read_assert_tag(f, 72)
                self.comp_min_ref = read_u32le(f)

                read_assert_tag(f, 66)
                self.has_comp_max_ref = read_bool(f)

                read_assert_tag(f, 72)
                self.comp_max_ref = read_u32le(f)

            elif tag == 0x03:
                read_assert_tag(f, 72)
                self.alpha_min_ref = read_u32le(f)

                read_assert_tag(f, 72)
                self.alpha_max_ref = read_u32le(f)

            else:
                raise ValueError("unknown ext tag 0x%02X %d" % (tag,tag))

        read_assert_tag(f, 0x03)
