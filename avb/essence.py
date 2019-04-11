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
    read_s8,     write_s8,
    read_s16le,  write_s16le,
    read_u16le,  write_u16le,
    read_u32le,  write_u32le,
    read_u32be,  write_u32be,
    read_s32le,  write_s32le,
    read_s64le,  write_s64le,
    read_u64le,  write_u64le,
    read_string, write_string,
    read_raw_uuid, write_raw_uuid,
    read_uuid,   write_uuid,
    reverse_str,
    read_exp10_encoded_float, write_exp10_encoded_float,
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
        AVBPropertyDef('mob_kind',       'OMFI:MDES:MobKind',         'int8',         0),
        AVBPropertyDef('locator',        'OMFI:MDES:Locator',         'reference', None),
        AVBPropertyDef('intermediate',   'OMFI:MDES:MC:Intermediate', 'bool',     False),
        AVBPropertyDef('physical_media', 'OMFI:MOBJ:PhysicalMedia',   'reference', None),
        AVBPropertyDef('uuid',           'OMFI:AMDL:acfUID',          'UUID'),
        AVBPropertyDef('wchar',          'OMFI:AMDL:acfWChar',        'bytes'),
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
            elif tag == 0x02:
                # this is utf-16 string data
                read_assert_tag(f, 65)
                size = read_s32le(f)
                self.wchar = bytearray(f.read(size))
            elif tag == 0x03:
                read_assert_tag(f, 72)
                self.attributes = read_object_ref(self.root, f)
            else:
                raise ValueError("%s: unknown ext tag 0x%02X %d" % (str(self.class_id), tag,tag))

        if self.class_id[:] == b'MDES':
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
            write_s32le(f, 16)
            write_raw_uuid(f, self.uuid)

        if hasattr(self, 'wchar'):
            write_u8(f, 0x01)
            write_u8(f, 0x02)
            write_u8(f, 65)
            write_s32le(f, len(self.wchar))
            f.write(self.wchar)

        if hasattr(self, 'attributes'):
            write_u8(f, 0x01)
            write_u8(f, 0x03)
            write_u8(f, 72)
            write_object_ref(self.root, f, self.attributes)

        if self.class_id[:] == b'MDES':
            write_u8(f, 0x03)


@utils.register_class
class TapeDescriptor(MediaDescriptor):
    class_id = b'MDTP'
    propertydefs = MediaDescriptor.propertydefs + [
        AVBPropertyDef('cframe', 'OMFI:MDTP:CFrame', "int16",  0)
    ]
    __slots__ = ()

    def read(self, f):
        super(TapeDescriptor, self).read(f)
        read_assert_tag(f, 0x02)
        read_assert_tag(f, 0x02)

        self.cframe = read_s16le(f)
        read_assert_tag(f, 0x03)

    def write(self, f):
        super(TapeDescriptor, self).write(f)
        write_u8(f, 0x02)
        write_u8(f, 0x02)

        write_s16le(f, self.cframe)
        write_u8(f, 0x03)

@utils.register_class
class FilmDescriptor(MediaDescriptor):
    class_id = b'MDFM'
    __slots__ = ()

    def read(self, f):
        super(FilmDescriptor, self).read(f)
        read_assert_tag(f, 0x02)
        read_assert_tag(f, 0x01)

        read_assert_tag(f, 0x03)

    def write(self, f):
        super(FilmDescriptor, self).write(f)
        write_u8(f, 0x02)
        write_u8(f, 0x01)
        write_u8(f, 0x03)

class MediaFileDescriptor(MediaDescriptor):
    class_id = b'MDFL'
    propertydefs = MediaDescriptor.propertydefs + [
        AVBPropertyDef('edit_rate',   'EdRate',               'fexp10', 25),
        AVBPropertyDef('length',      'OMFI:MDFL:Length',     'int32',   0),
        AVBPropertyDef('is_omfi',     'OMFI:MDFL:IsOMFI',     'int16',   0),
        AVBPropertyDef('data_offset', 'OMFI:MDFL:dataOffset', 'int32',   0),
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

    def write(self, f):
        super(MediaFileDescriptor, self).write(f)
        write_u8(f, 0x02)
        write_u8(f, 0x03)

        write_exp10_encoded_float(f, self.edit_rate)
        write_s32le(f, self.length)
        write_s16le(f, self.is_omfi)
        write_s32le(f, self.data_offset)

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
        self.descriptors = AVBRefList.__new__(AVBRefList, root=self.root)
        for i in range(count):
            ref = read_object_ref(self.root, f)
            self.descriptors.append(ref)

        read_assert_tag(f, 0x03)

    def write(self, f):
        super(MultiDescriptor, self).write(f)
        write_u8(f, 0x02)
        write_u8(f, 0x01)

        write_s32le(f, len(self.descriptors))

        for descriptor in self.descriptors:
            write_object_ref(self.root, f, descriptor)

        write_u8(f, 0x03)

@utils.register_class
class WaveDescriptor(MediaFileDescriptor):
    class_id = b'WAVE'
    propertydefs = MediaFileDescriptor.propertydefs + [
        AVBPropertyDef('summary',   'OMFI:WAVD:Summary',   'bytes'),
    ]
    def read(self, f):
        super(WaveDescriptor, self).read(f)
        read_assert_tag(f, 0x02)
        read_assert_tag(f, 0x01)

        assert f.read(4) == b'RIFF'

        size = read_u32le(f)
        self.summary = bytearray(f.read(size))
        read_assert_tag(f, 0x03)

    def write(self, f):
        super(WaveDescriptor, self).write(f)
        write_u8(f, 0x02)
        write_u8(f, 0x01)
        f.write(b'RIFF')
        write_u32le(f, len(self.summary))
        f.write(self.summary)
        write_u8(f, 0x03)

@utils.register_class
class AIFCDescriptor(MediaFileDescriptor):
    class_id = b'AIFC'
    propertydefs = MediaFileDescriptor.propertydefs + [
        AVBPropertyDef('summary',   'OMFI:AIFD:Summary',   'bytes'),
        AVBPropertyDef('data_pos',  'OMFI:AIFD:MC:DataPos', 'int32'),
    ]
    def read(self, f):
        super(AIFCDescriptor, self).read(f)
        read_assert_tag(f, 0x02)
        read_assert_tag(f, 0x01)

        assert f.read(4) == b'FORM'
        size = read_u32be(f)
        self.summary = bytearray(f.read(size))
        for tag in iter_ext(f):
            if tag == 0x01:
                read_assert_tag(f, 71)
                self.data_pos = read_s32le(f)
            else:
                raise ValueError("%s: unknown ext tag 0x%02X %d" % (str(self.class_id), tag,tag))

        read_assert_tag(f, 0x03)

    def write(self, f):
        super(AIFCDescriptor, self).write(f)
        write_u8(f, 0x02)
        write_u8(f, 0x01)

        f.write(b'FORM')
        write_u32be(f, len(self.summary))
        f.write(self.summary)

        if hasattr(self, 'data_pos'):
            write_u8(f, 0x01)
            write_u8(f, 0x01)
            write_u8(f, 71)
            write_s32le(f, self.data_pos)

        write_u8(f, 0x03)

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
        AVBPropertyDef('ebu_timestamp',               'OMFI:PCMA:SmpteEbuTimestamp',         'int64'),
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

        for tag in iter_ext(f):
            if tag == 0x01:
                read_assert_tag(f, 77)
                self.ebu_timestamp = read_s64le(f)
            else:
                raise ValueError("%s: unknown ext tag 0x%02X %d" % (str(self.class_id), tag,tag))

        read_assert_tag(f, 0x03)

    def write(self, f):
        super(PCMADescriptor, self).write(f)
        write_u8(f, 0x02)
        write_u8(f, 0x01)

        write_u16le(f, self.channels)
        write_u16le(f, self.quantization_bits)
        write_exp10_encoded_float(f, self.sample_rate)

        write_bool(f, self.locked)
        write_s16le(f, self.audio_ref_level)
        write_s32le(f, self.electro_spatial_formulation)
        write_u16le(f, self.dial_norm)

        write_u32le(f, self.coding_format)
        write_u32le(f, self.block_align)

        write_u16le(f, self.sequence_offset)
        write_u32le(f, self.average_bps)
        write_bool(f, self.has_peak_envelope_data)

        write_s32le(f, self.peak_envelope_version)
        write_s32le(f, self.peak_envelope_format)
        write_s32le(f, self.points_per_peak_value)
        write_s32le(f, self.peak_envelope_block_size)
        write_s32le(f, self.peak_channel_count)
        write_s32le(f, self.peak_frame_count)
        write_u64le(f, self.peak_of_peaks_offset)
        write_s32le(f, self.peak_envelope_timestamp)

        if hasattr(self, 'ebu_timestamp'):
            write_u8(f, 0x01)
            write_u8(f, 0x01)
            write_u8(f, 77)
            write_s64le(f, self.ebu_timestamp)

        write_u8(f, 0x03)

@utils.register_class
class DIDDescriptor(MediaFileDescriptor):
    class_id = b'DIDD'
    propertydefs = MediaFileDescriptor.propertydefs + [
        AVBPropertyDef('stored_height',              'OMFI:DIDD:StoredHeight',                            'int32',    1080),
        AVBPropertyDef('stored_width',               'OMFI:DIDD:StoredWidth',                             'int32',    1920),
        AVBPropertyDef('sampled_height',             'OMFI:DIDD:SampledHeight',                           'int32',    1080),
        AVBPropertyDef('sampled_width',              'OMFI:DIDD:SampledWidth',                            'int32',    1920),
        AVBPropertyDef('sampled_x_offset',           'OMFI:DIDD:SampledXOffset',                          'int32',       0),
        AVBPropertyDef('sampled_y_offset',           'OMFI:DIDD:SampledYOffset',                          'int32',       0),
        AVBPropertyDef('display_height',             'OMFI:DIDD:DisplayHeight',                           'int32',    1080),
        AVBPropertyDef('display_width',              'OMFI:DIDD:DisplayWidth',                            'int32',    1920),
        AVBPropertyDef('display_x_offset',           'OMFI:DIDD:DisplayXOffset',                          'int32',       0),
        AVBPropertyDef('display_y_offset',           'OMFI:DIDD:DisplayYOffset',                          'int32',       0),
        AVBPropertyDef('frame_layout',               'OMFI:DIDD:FrameLayout',                             'int16',       0),
        AVBPropertyDef('aspect_ratio',               'OMFI:DIDD:ImageAspectRatio',                        'rational',   [16,9]),
        AVBPropertyDef('line_map',                   'OMFI:DIDD:VideoLineMap',                            'list',       [42,0]),
        AVBPropertyDef('alpha_transparency',         'OMFI:DIDD:AlphaTransparency',                       'int32',       0),
        AVBPropertyDef('uniformness',                'OMFI:DIDD:Uniformness',                             'bool',    False),
        AVBPropertyDef('did_image_size',             'OMFI:DIDD:DIDImageSize',                            'int32', 108511232),
        AVBPropertyDef('next_did_desc',              "OMFI:DIDD:NextDIDDesc",                         'reference',    None),
        AVBPropertyDef('compress_method',            'OMFI:DIDD:DIDCompressMethod',                       'bytes', b'AVHD'),
        AVBPropertyDef('resolution_id',              'OMFI:DIDD:DIDResolutionID',                         'int32',    1237),
        AVBPropertyDef('image_alignment_factor',     'OMFI:DIDD:ImageAlignmentFactor',                    'int32',    8192),
        AVBPropertyDef('frame_index_byte_order',     'OMFI:DIDD:FrameIndexByteOrder',                     'int16'),
        AVBPropertyDef('frame_sample_size',          'OMFI:DIDD:FrameSampleSize',                         'int32'),
        AVBPropertyDef('first_frame_offset',         'OMFI:DIDD:FirstFrameOffset',                        'int32'),
        AVBPropertyDef('client_fill_start',          'OMFI:DIDD:ClientFillStart',                         'int32'),
        AVBPropertyDef('client_fill_end',            'OMFI:DIDD:ClientFillEnd',                           'int32'),
        AVBPropertyDef('offset_to_rle_frame_index',  'OMFI:DIDD:OffsetToRLEFrameIndexes',                 'int32'),
        AVBPropertyDef('frame_start_offset',         'OMFI:DIDD:FrameStartOffset',                        'int32'),
        AVBPropertyDef('valid_box',                  'OMFI:DIDD:Valid',                                   'bounds_box'),
        AVBPropertyDef('essence_box',                'OMFI:DIDD:Essence',                                 'bounds_box'),
        AVBPropertyDef('source_box',                 'OMFI:DIDD:Source',                                  'bounds_box'),
        AVBPropertyDef('framing_box',                'OMFI:DIDD:Framing',                                 'bounds_box'),
        AVBPropertyDef('reformatting_option',        'OMFI:DIDD:ReformattingOption',                      'int32'),
        AVBPropertyDef('transfer_characteristic',    'OMFI:DIDD:TransferCharacteristic',                  'UUID'),
        AVBPropertyDef('color_primaries',            'OMFI:DIDD:ColorPrimaries',                          'UUID'),
        AVBPropertyDef('coding_equations',           'OMFI:DIDD:CodingEquations',                         'UUID'),
        AVBPropertyDef('essence_compression',        'OMFI:DIDD:EssenceCompression',                      'UIDD'),
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

            elif tag == 0x06:
                read_assert_tag(f, 71)
                self.frame_start_offset = read_s32le(f)

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
            elif tag == 12:
                read_assert_tag(f, 80)
                self.essence_compression = read_raw_uuid(f)
            elif tag == 15:
                read_assert_tag(f, 66)
                self.frame_checked_with_mapper = read_bool(f)

            else:
                raise ValueError("%s: unknown ext tag 0x%02X %d" % (str(self.class_id), tag,tag))

        if self.class_id[:] == b'DIDD':
            read_assert_tag(f, 0x03)

    def write(self, f):
        super(DIDDescriptor, self).write(f)
        write_u8(f, 0x02)
        write_u8(f, 0x02)

        write_s32le(f, self.stored_height)
        write_s32le(f, self.stored_width)

        write_s32le(f, self.sampled_height)
        write_s32le(f, self.sampled_width)

        write_s32le(f, self.sampled_x_offset)
        write_s32le(f, self.sampled_y_offset)

        write_s32le(f, self.display_height)
        write_s32le(f, self.display_width)

        write_s32le(f, self.display_x_offset)
        write_s32le(f, self.display_y_offset)

        write_s16le(f, self.frame_layout)

        write_s32le(f, self.aspect_ratio[0])
        write_s32le(f, self.aspect_ratio[1])

        write_s32le(f, len(self.line_map) * 4)
        for i in self.line_map:
            write_s32le(f, i)


        write_s32le(f, self.alpha_transparency)
        write_bool(f, self.uniformness)

        write_s32le(f, self.did_image_size)

        write_object_ref(self.root, f, self.next_did_desc)

        compress_method =  reverse_str(self.compress_method)
        assert len(compress_method) == 4
        f.write(compress_method)

        write_s32le(f, self.resolution_id)
        write_s32le(f, self.image_alignment_factor)

        if hasattr(self, 'frame_index_byte_order'):
            write_u8(f, 0x01)
            write_u8(f, 0x01)
            write_u8(f, 69)
            write_s16le(f, self.frame_index_byte_order)

        if hasattr(self, 'frame_sample_size'):
            write_u8(f, 0x01)
            write_u8(f, 0x02)
            write_u8(f, 71)
            write_s32le(f, self.frame_sample_size)

        if hasattr(self, 'first_frame_offset'):
            write_u8(f, 0x01)
            write_u8(f, 0x03)
            write_u8(f, 71)
            write_s32le(f, self.first_frame_offset)

        if hasattr(self, 'client_fill_start'):
            write_u8(f, 0x01)
            write_u8(f, 0x04)
            write_u8(f, 71)
            write_s32le(f, self.client_fill_start)

            write_u8(f, 71)
            write_s32le(f, self.client_fill_end)

        if hasattr(self, 'offset_to_rle_frame_index'):
            write_u8(f, 0x01)
            write_u8(f, 0x05)
            write_u8(f, 71)
            write_s32le(f, self.offset_to_rle_frame_index)

        if hasattr(self, 'frame_start_offset'):
            write_u8(f, 0x01)
            write_u8(f, 0x06)
            write_u8(f, 71)
            write_s32le(f, self.frame_start_offset)

        if hasattr(self, 'valid_box') and hasattr(self, 'essence_box') and hasattr(self, 'source_box'):
            write_u8(f, 0x01)
            write_u8(f, 0x08)

            write_u8(f, 71)
            write_s32le(f, self.valid_box[0][0])
            write_u8(f, 71)
            write_s32le(f, self.valid_box[0][1])

            write_u8(f, 71)
            write_s32le(f, self.valid_box[1][0])
            write_u8(f, 71)
            write_s32le(f, self.valid_box[1][1])

            write_u8(f, 71)
            write_s32le(f, self.valid_box[2][0])
            write_u8(f, 71)
            write_s32le(f, self.valid_box[2][1])

            write_u8(f, 71)
            write_s32le(f, self.valid_box[3][0])
            write_u8(f, 71)
            write_s32le(f, self.valid_box[3][1])

            # essence
            write_u8(f, 71)
            write_s32le(f, self.essence_box[0][0])
            write_u8(f, 71)
            write_s32le(f, self.essence_box[0][1])


            write_u8(f, 71)
            write_s32le(f, self.essence_box[1][0])
            write_u8(f, 71)
            write_s32le(f, self.essence_box[1][1])

            write_u8(f, 71)
            write_s32le(f, self.essence_box[2][0])
            write_u8(f, 71)
            write_s32le(f, self.essence_box[2][1])

            write_u8(f, 71)
            write_s32le(f, self.essence_box[3][0])
            write_u8(f, 71)
            write_s32le(f, self.essence_box[3][1])

            # source
            write_u8(f, 71)
            write_s32le(f, self.source_box[0][0])
            write_u8(f, 71)
            write_s32le(f, self.source_box[0][1])

            write_u8(f, 71)
            write_s32le(f, self.source_box[1][0])
            write_u8(f, 71)
            write_s32le(f, self.source_box[1][1])

            write_u8(f, 71)
            write_s32le(f, self.source_box[2][0])
            write_u8(f, 71)
            write_s32le(f, self.source_box[2][1])

            write_u8(f, 71)
            write_s32le(f, self.source_box[3][0])
            write_u8(f, 71)
            write_s32le(f, self.source_box[3][1])

        if hasattr(self, 'framing_box') and hasattr(self, 'reformatting_option'):
            write_u8(f, 0x01)
            write_u8(f, 9)

            # print("\n??!", peek_data(f).encode('hex'), '\n')
            write_u8(f, 71)
            write_s32le(f, self.framing_box[0][0])
            write_u8(f, 71)
            write_s32le(f, self.framing_box[0][1])

            write_u8(f, 71)
            write_s32le(f, self.framing_box[1][0])
            write_u8(f, 71)
            write_s32le(f, self.framing_box[1][1])

            write_u8(f, 71)
            write_s32le(f, self.framing_box[2][0])
            write_u8(f, 71)
            write_s32le(f, self.framing_box[2][1])

            write_u8(f, 71)
            write_s32le(f, self.framing_box[3][0])
            write_u8(f, 71)
            write_s32le(f, self.framing_box[3][1])

            write_u8(f, 71)
            write_s32le(f, self.reformatting_option)

        if hasattr(self, 'transfer_characteristic'):
            write_u8(f, 0x01)
            write_u8(f, 10)
            write_u8(f, 80)
            write_raw_uuid(f, self.transfer_characteristic)

        if hasattr(self, 'color_primaries') and hasattr(self, 'coding_equations'):
            write_u8(f, 0x01)
            write_u8(f, 11)
            write_u8(f, 80)
            write_raw_uuid(f, self.color_primaries)
            write_u8(f, 80)
            write_raw_uuid(f, self.coding_equations)

        if hasattr(self, 'essence_compression'):
            write_u8(f, 0x01)
            write_u8(f, 12)
            write_u8(f, 80)
            write_raw_uuid(f, self.essence_compression)

        if hasattr(self, 'frame_checked_with_mapper'):
            write_u8(f, 0x01)
            write_u8(f, 15)
            write_u8(f, 66)
            write_bool(f, self.frame_checked_with_mapper)

        if self.class_id[:] == b'DIDD':
            write_u8(f, 0x03)

@utils.register_class
class CDCIDescriptor(DIDDescriptor):
    class_id = b'CDCI'
    propertydefs = DIDDescriptor.propertydefs + [
        AVBPropertyDef('horizontal_subsampling', 'OMFI:CDCI:HorizontalSubsampling',         'uint32',   2),
        AVBPropertyDef('vertical_subsampling',   'OMFI:CDCI:VerticalSubsampling',           'uint32',   1),
        AVBPropertyDef('component_width',        'OMFI:CDCI:ComponentWidth',                'int32',    8),
        AVBPropertyDef('color_sitting',          'OMFI:CDCI:ColorSiting',                   'int16',    4),
        AVBPropertyDef('black_ref_level',        'OMFI:CDCI:BlackReferenceLevel',           'uint32',  16),
        AVBPropertyDef('white_ref_level',        'OMFI:CDCI:WhiteReferenceLevel',           'uint32', 235),
        AVBPropertyDef('color_range',            'OMFI:CDCI:ColorRange',                    'uint32', 255),
        AVBPropertyDef('frame_index_offset',     'OMFI:JPED:OffsetToFrameIndexes',          'uint64',   0),
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

        if self.class_id[:] == b'CDCI':
            read_assert_tag(f, 0x03)

    def write(self, f):
        super(CDCIDescriptor, self).write(f)
        write_u8(f, 0x02)
        write_u8(f, 0x02)

        write_u32le(f, self.horizontal_subsampling)
        write_u32le(f, self.vertical_subsampling)
        write_s32le(f, self.component_width)

        write_s16le(f, self.color_sitting)
        write_u32le(f, self.black_ref_level)
        write_u32le(f, self.white_ref_level)
        write_u32le(f, self.color_range)

        write_s64le(f, self.frame_index_offset)

        if hasattr(self, 'alpha_sampled_width'):
            write_u8(f, 0x01)
            write_u8(f, 0x01)
            write_u8(f, 72)
            write_u32le(f, self.alpha_sampled_width)

        if hasattr(self, 'ignore_bw'):
            write_u8(f, 0x01)
            write_u8(f, 0x02)
            write_u8(f, 72)
            write_u32le(f, self.ignore_bw)

        if self.class_id[:] == b'CDCI':
            write_u8(f, 0x03)

@utils.register_class
class MPGIDescriptor(CDCIDescriptor):
    class_id = b'MPGI'
    propertydefs = CDCIDescriptor.propertydefs + [
        AVBPropertyDef('mpeg_version',     "OMFI:MPGI:MPEGVersion",        "uint8"),
        AVBPropertyDef('profile',          "OMFI:MPGI:ProfileAndLevel",    "uint8"),
        AVBPropertyDef('gop_structure',    "OMFI:MPGI:GOPStructure",       "uint8"),
        AVBPropertyDef('stream_type',      "OMFI:MPGI:StreamType",         "uint8"),
        AVBPropertyDef('random_access',    "OMFI:MPGI:RandomAccess",       "bool"),
        AVBPropertyDef('leading_discard',  "OMFI:MPGI:LeadingDiscard",     "bool"),
        AVBPropertyDef('trailing_discard', "OMFI:MPGI:TrailingDiscard",    "bool"),
        AVBPropertyDef('min_gop_length',   "OMFI:MPGI:omMPGIMinGOPLength", "uint16"),
        AVBPropertyDef('max_gop_length',   "OMFI:MPGI:omMPGIMaxGOPLength", "uint16"),
        AVBPropertyDef('sequence_hdrlen',  "OMFI:MPGI:SequenceHdrLen",     "int32"),
    ]
    def read(self, f):
        super(MPGIDescriptor, self).read(f)

        read_assert_tag(f, 0x02)
        read_assert_tag(f, 0x01)

        self.mpeg_version = read_u8(f)
        self.profile = read_u8(f)
        self.gop_structure = read_u8(f)
        self.stream_type = read_u8(f)
        self.random_access = read_bool(f)
        self.leading_discard = read_bool(f)
        self.trailing_discard = read_bool(f)
        self.min_gop_length = read_u16le(f)
        self.max_gop_length = read_u16le(f)
        self.sequence_hdrlen = read_u32le(f)

        read_assert_tag(f, 0x03)

    def write(self, f):
        super(MPGIDescriptor, self).write(f)
        write_u8(f, 0x02)
        write_u8(f, 0x01)

        write_u8(f, self.mpeg_version)
        write_u8(f, self.profile)
        write_u8(f, self.gop_structure)
        write_u8(f, self.stream_type)
        write_bool(f, self.random_access)
        write_bool(f, self.leading_discard)
        write_bool(f, self.trailing_discard)
        write_u16le(f, self.min_gop_length)
        write_u16le(f, self.max_gop_length)
        write_u32le(f, self.sequence_hdrlen)

        write_u8(f, 0x03)

@utils.register_class
class JPEGDescriptor(CDCIDescriptor):
    class_id = b'JPED'
    propertydefs = CDCIDescriptor.propertydefs + [
        AVBPropertyDef('jpeg_table_id',           "OMFI:JPED:JPEGTableID",           "int32"),
        AVBPropertyDef('jpeg_frame_index_offset', "OMFI:JPED:OffsetToFrameIndexes",  "uint64"),
        AVBPropertyDef('quantization_tables',     "OMFI:JPED:QuantizationTables",    "bytes"),
        AVBPropertyDef('image_start_align',       "OMFI:JPED:ImageStartAlignment",   "int32"),
    ]

    def read(self, f):
        super(JPEGDescriptor, self).read(f)
        read_assert_tag(f, 0x02)
        read_assert_tag(f, 0x01)

        self.jpeg_table_id = read_s32le(f)
        self.jpeg_frame_index_offset = read_u64le(f)
        table_size = read_s32le(f)
        assert table_size >= 0
        self.quantization_tables = bytearray(f.read(table_size))

        for tag in iter_ext(f):
            if tag == 0x01:
                read_assert_tag(f, 71)
                self.image_start_align = read_s32le(f)
            else:
                raise ValueError("unknown ext tag 0x%02X %d" % (tag,tag))

        read_assert_tag(f, 0x03)

    def write(self, f):
        super(JPEGDescriptor, self).write(f)
        write_u8(f, 0x02)
        write_u8(f, 0x01)

        write_s32le(f, self.jpeg_table_id)
        write_u64le(f, self.jpeg_frame_index_offset)
        write_s32le(f, len(self.quantization_tables))
        f.write(self.quantization_tables)

        if hasattr(self, 'image_start_align'):
            write_u8(f, 0x01)
            write_u8(f, 0x01)
            write_u8(f, 71)
            write_s32le(f, self.image_start_align)

        write_u8(f, 0x03)

def encode_pixel_layout(layout):
    pixel_layout = BytesIO()
    pixel_struct = BytesIO()

    for i in range(len(layout)):
        write_u8(pixel_layout, layout[i]['Code'])
        write_u8(pixel_struct, layout[i]['Size'])

    return pixel_layout.getvalue(), pixel_struct.getvalue()

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
        pixel_layout = bytearray(f.read(layout_size))

        struct_size =  read_u32le(f)
        pixel_struct = bytearray(f.read(struct_size))

        assert layout_size == struct_size

        layout = []
        for code, size in zip(pixel_layout, pixel_struct):
            layout.append({'Code': code, "Size" : size})

        self.pixel_layout = layout

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

    def write(self, f):
        super(RGBADescriptor, self).write(f)
        write_u8(f, 0x02)
        write_u8(f, 0x01)

        pixel_layout, pixel_struct = encode_pixel_layout(self.pixel_layout)

        # this seems to be encode the same way as in AAF
        write_u32le(f, len(pixel_layout))
        f.write(pixel_layout)

        write_u32le(f, len(pixel_struct))
        f.write(pixel_struct)

        # palette_layout_size
        write_u32le(f, 0)
        # palette_struct_size
        write_u32le(f, 0)
        # palette_size
        write_u32le(f, 0)


        if hasattr(self, 'frame_index_offset'):
            write_u8(f, 0x01)
            write_u8(f, 0x01)
            write_u8(f, 77)
            write_u64le(f, self.frame_index_offset)

        if hasattr(self, 'has_comp_min_ref'):
            write_u8(f, 0x01)
            write_u8(f, 0x02)
            write_u8(f, 66)
            write_bool(f, self.has_comp_min_ref)

            write_u8(f, 72)
            write_u32le(f, self.comp_min_ref)

            write_u8(f, 66)
            write_bool(f, self.has_comp_max_ref)

            write_u8(f, 72)
            write_u32le(f, self.comp_max_ref)

        if hasattr(self, 'alpha_min_ref'):
            write_u8(f, 0x01)
            write_u8(f, 0x03)
            write_u8(f, 72)
            write_u32le(f, self.alpha_min_ref)

            write_u8(f, 72)
            write_u32le(f, self.alpha_max_ref)

        write_u8(f, 0x03)
