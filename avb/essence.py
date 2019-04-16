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
from . utils import peek_data

@utils.register_class
class MediaDescriptor(core.AVBObject):
    class_id = b'MDES'
    propertydefs_dict = {}
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
        ctx = self.root.ictx
        ctx.read_assert_tag(f, 0x02)
        ctx.read_assert_tag(f, 0x03)

        self.mob_kind = ctx.read_u8(f)
        self.locator = []
        self.locator = ctx.read_object_ref(self.root, f)
        self.intermediate = ctx.read_bool(f)
        self.physical_media = ctx.read_object_ref(self.root, f)

        # print('sss', self.locator)
        # print(peek_data(f).encode('hex'))

        for tag in ctx.iter_ext(f):

            if tag == 0x01:
                ctx.read_assert_tag(f, 65)
                uuid_len = ctx.read_s32(f)
                assert uuid_len == 16
                self.uuid = ctx.read_raw_uuid(f)
            elif tag == 0x02:
                # this is utf-16 string data
                ctx.read_assert_tag(f, 65)
                size = ctx.read_s32(f)
                self.wchar = bytearray(f.read(size))
            elif tag == 0x03:
                ctx.read_assert_tag(f, 72)
                self.attributes = ctx.read_object_ref(self.root, f)
            else:
                raise ValueError("%s: unknown ext tag 0x%02X %d" % (str(self.class_id), tag,tag))

        if self.class_id[:] == b'MDES':
            ctx.read_assert_tag(f, 0x03)

    def write(self, f):
        super(MediaDescriptor, self).write(f)
        ctx = self.root.octx
        ctx.write_u8(f, 0x02)
        ctx.write_u8(f, 0x03)

        ctx.write_u8(f, self.mob_kind)
        ctx.write_object_ref(self.root, f, self.locator)
        ctx.write_bool(f, self.intermediate)
        ctx.write_object_ref(self.root, f, self.physical_media)

        if hasattr(self, 'uuid'):
            ctx.write_u8(f, 0x01)
            ctx.write_u8(f, 0x01)
            ctx.write_u8(f, 65)
            ctx.write_s32(f, 16)
            ctx.write_raw_uuid(f, self.uuid)

        if hasattr(self, 'wchar'):
            ctx.write_u8(f, 0x01)
            ctx.write_u8(f, 0x02)
            ctx.write_u8(f, 65)
            ctx.write_s32(f, len(self.wchar))
            f.write(self.wchar)

        if hasattr(self, 'attributes'):
            ctx.write_u8(f, 0x01)
            ctx.write_u8(f, 0x03)
            ctx.write_u8(f, 72)
            ctx.write_object_ref(self.root, f, self.attributes)

        if self.class_id[:] == b'MDES':
            ctx.write_u8(f, 0x03)


@utils.register_class
class TapeDescriptor(MediaDescriptor):
    class_id = b'MDTP'
    propertydefs = MediaDescriptor.propertydefs + [
        AVBPropertyDef('cframe', 'OMFI:MDTP:CFrame', "int16",  0)
    ]
    __slots__ = ()

    def read(self, f):
        super(TapeDescriptor, self).read(f)
        ctx = self.root.ictx
        ctx.read_assert_tag(f, 0x02)
        ctx.read_assert_tag(f, 0x02)

        self.cframe = ctx.read_s16(f)
        ctx.read_assert_tag(f, 0x03)

    def write(self, f):
        super(TapeDescriptor, self).write(f)
        ctx = self.root.octx
        ctx.write_u8(f, 0x02)
        ctx.write_u8(f, 0x02)

        ctx.write_s16(f, self.cframe)
        ctx.write_u8(f, 0x03)

@utils.register_class
class FilmDescriptor(MediaDescriptor):
    class_id = b'MDFM'
    __slots__ = ()

    def read(self, f):
        super(FilmDescriptor, self).read(f)
        ctx = self.root.ictx
        ctx.read_assert_tag(f, 0x02)
        ctx.read_assert_tag(f, 0x01)

        ctx.read_assert_tag(f, 0x03)

    def write(self, f):
        super(FilmDescriptor, self).write(f)
        ctx = self.root.octx
        ctx.write_u8(f, 0x02)
        ctx.write_u8(f, 0x01)
        ctx.write_u8(f, 0x03)

@utils.register_class
class NagraDescriptor(MediaDescriptor):
    class_id = b'MDNG'
    __slots__ = ()

    def read(self, f):
        super(NagraDescriptor, self).read(f)
        ctx = self.root.ictx
        ctx.read_assert_tag(f, 0x02)
        ctx.read_assert_tag(f, 0x01)

        ctx.read_assert_tag(f, 0x03)

    def write(self, f):
        super(NagraDescriptor, self).write(f)
        ctx = self.root.octx
        ctx.write_u8(f, 0x02)
        ctx.write_u8(f, 0x01)
        ctx.write_u8(f, 0x03)

@utils.register_class
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
        ctx = self.root.ictx
        ctx.read_assert_tag(f, 0x02)
        ctx.read_assert_tag(f, 0x03)

        self.edit_rate = ctx.read_exp10_encoded_float(f)
        self.length = ctx.read_s32(f)
        self.is_omfi = ctx.read_s16(f)
        self.data_offset = ctx.read_s32(f)

        if self.class_id[:] == b'MDFL':
            ctx.read_assert_tag(f, 0x03)

    def write(self, f):
        super(MediaFileDescriptor, self).write(f)
        ctx = self.root.octx
        ctx.write_u8(f, 0x02)
        ctx.write_u8(f, 0x03)

        ctx.write_exp10_encoded_float(f, self.edit_rate)
        ctx.write_s32(f, self.length)
        ctx.write_s16(f, self.is_omfi)
        ctx.write_s32(f, self.data_offset)

        if self.class_id[:] == b'MDFL':
            ctx.write_u8(f, 0x03)

@utils.register_class
class MultiDescriptor(MediaFileDescriptor):
    class_id = b'MULD'
    propertydefs = MediaFileDescriptor.propertydefs + [
        AVBPropertyDef('descriptors', 'OMFI:MULD:Descriptors', "ref_list"),
    ]
    __slots__ = ()

    def read(self, f):
        super(MultiDescriptor, self).read(f)
        ctx = self.root.ictx
        ctx.read_assert_tag(f, 0x02)
        ctx.read_assert_tag(f, 0x01)

        count = ctx.read_s32(f)
        self.descriptors = AVBRefList.__new__(AVBRefList, root=self.root)
        for i in range(count):
            ref = ctx.read_object_ref(self.root, f)
            self.descriptors.append(ref)

        ctx.read_assert_tag(f, 0x03)

    def write(self, f):
        super(MultiDescriptor, self).write(f)
        ctx = self.root.octx
        ctx.write_u8(f, 0x02)
        ctx.write_u8(f, 0x01)

        ctx.write_s32(f, len(self.descriptors))

        for descriptor in self.descriptors:
            ctx.write_object_ref(self.root, f, descriptor)

        ctx.write_u8(f, 0x03)

@utils.register_class
class WaveDescriptor(MediaFileDescriptor):
    class_id = b'WAVE'
    propertydefs = MediaFileDescriptor.propertydefs + [
        AVBPropertyDef('summary',   'OMFI:WAVD:Summary',   'bytes'),
    ]
    __slots__ = ()

    def read(self, f):
        super(WaveDescriptor, self).read(f)
        ctx = self.root.ictx
        ctx.read_assert_tag(f, 0x02)
        ctx.read_assert_tag(f, 0x01)

        assert f.read(4) == b'RIFF'

        # NOTE: this is suppose to be LE
        size = ctx.read_u32le(f)
        self.summary = bytearray(f.read(size))
        ctx.read_assert_tag(f, 0x03)

    def write(self, f):
        super(WaveDescriptor, self).write(f)
        ctx = self.root.octx
        ctx.write_u8(f, 0x02)
        ctx.write_u8(f, 0x01)
        f.write(b'RIFF')
        # NOTE: this is suppose to be LE
        ctx.write_u32le(f, len(self.summary))
        f.write(self.summary)
        ctx.write_u8(f, 0x03)

@utils.register_class
class AIFCDescriptor(MediaFileDescriptor):
    class_id = b'AIFC'
    propertydefs = MediaFileDescriptor.propertydefs + [
        AVBPropertyDef('summary',   'OMFI:AIFD:Summary',   'bytes'),
        AVBPropertyDef('data_pos',  'OMFI:AIFD:MC:DataPos', 'int32'),
    ]
    __slots__ = ()

    def read(self, f):
        super(AIFCDescriptor, self).read(f)
        ctx = self.root.ictx
        ctx.read_assert_tag(f, 0x02)
        ctx.read_assert_tag(f, 0x01)

        assert f.read(4) == b'FORM'

        # NOTE: this is suppose to be BE
        size = ctx.read_u32be(f)
        self.summary = bytearray(f.read(size))
        for tag in ctx.iter_ext(f):
            if tag == 0x01:
                ctx.read_assert_tag(f, 71)
                self.data_pos = ctx.read_s32(f)
            else:
                raise ValueError("%s: unknown ext tag 0x%02X %d" % (str(self.class_id), tag,tag))

        ctx.read_assert_tag(f, 0x03)

    def write(self, f):
        super(AIFCDescriptor, self).write(f)
        ctx = self.root.octx
        ctx.write_u8(f, 0x02)
        ctx.write_u8(f, 0x01)

        f.write(b'FORM')
        # NOTE: this is suppose to be BE
        ctx.write_u32be(f, len(self.summary))
        f.write(self.summary)

        if hasattr(self, 'data_pos'):
            ctx.write_u8(f, 0x01)
            ctx.write_u8(f, 0x01)
            ctx.write_u8(f, 71)
            ctx.write_s32(f, self.data_pos)

        ctx.write_u8(f, 0x03)

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
        AVBPropertyDef('timecode_framerate',          'OMFI:PCMA:TimecodeFrameRate',        'string'),
    ]
    __slots__ = ()

    def read(self, f):
        super(PCMADescriptor, self).read(f)
        ctx = self.root.ictx
        ctx.read_assert_tag(f, 0x02)
        ctx.read_assert_tag(f, 0x01)

        self.channels = ctx.read_u16(f)
        self.quantization_bits = ctx.read_u16(f)
        self.sample_rate = ctx.read_exp10_encoded_float(f)

        self.locked = ctx.read_bool(f)
        self.audio_ref_level = ctx.read_s16(f)
        self.electro_spatial_formulation = ctx.read_s32(f)
        self.dial_norm = ctx.read_u16(f)

        self.coding_format = ctx.read_u32(f)
        self.block_align = ctx.read_u32(f)

        self.sequence_offset = ctx.read_u16(f)
        self.average_bps = ctx.read_u32(f)
        self.has_peak_envelope_data = ctx.read_bool(f)

        self.peak_envelope_version = ctx.read_s32(f)
        self.peak_envelope_format = ctx.read_s32(f)
        self.points_per_peak_value = ctx.read_s32(f)
        self.peak_envelope_block_size = ctx.read_s32(f)
        self.peak_channel_count = ctx.read_s32(f)
        self.peak_frame_count = ctx.read_s32(f)
        self.peak_of_peaks_offset = ctx.read_u64(f)
        self.peak_envelope_timestamp = ctx.read_s32(f)

        for tag in ctx.iter_ext(f):
            if tag == 0x01:
                ctx.read_assert_tag(f, 77)
                self.ebu_timestamp = ctx.read_s64(f)
            elif tag == 0x03:
                ctx.read_assert_tag(f, 76)
                # yes this is a string!
                self.timecode_framerate = ctx.read_string(f)
            else:
                raise ValueError("%s: unknown ext tag 0x%02X %d" % (str(self.class_id), tag,tag))

        ctx.read_assert_tag(f, 0x03)

    def write(self, f):
        super(PCMADescriptor, self).write(f)
        ctx = self.root.octx
        ctx.write_u8(f, 0x02)
        ctx.write_u8(f, 0x01)

        ctx.write_u16(f, self.channels)
        ctx.write_u16(f, self.quantization_bits)
        ctx.write_exp10_encoded_float(f, self.sample_rate)

        ctx.write_bool(f, self.locked)
        ctx.write_s16(f, self.audio_ref_level)
        ctx.write_s32(f, self.electro_spatial_formulation)
        ctx.write_u16(f, self.dial_norm)

        ctx.write_u32(f, self.coding_format)
        ctx.write_u32(f, self.block_align)

        ctx.write_u16(f, self.sequence_offset)
        ctx.write_u32(f, self.average_bps)
        ctx.write_bool(f, self.has_peak_envelope_data)

        ctx.write_s32(f, self.peak_envelope_version)
        ctx.write_s32(f, self.peak_envelope_format)
        ctx.write_s32(f, self.points_per_peak_value)
        ctx.write_s32(f, self.peak_envelope_block_size)
        ctx.write_s32(f, self.peak_channel_count)
        ctx.write_s32(f, self.peak_frame_count)
        ctx.write_u64(f, self.peak_of_peaks_offset)
        ctx.write_s32(f, self.peak_envelope_timestamp)

        if hasattr(self, 'ebu_timestamp'):
            ctx.write_u8(f, 0x01)
            ctx.write_u8(f, 0x01)
            ctx.write_u8(f, 77)
            ctx.write_s64(f, self.ebu_timestamp)

        if hasattr(self, 'timecode_framerate'):
            ctx.write_u8(f, 0x01)
            ctx.write_u8(f, 0x03)
            ctx.write_u8(f, 76)
            ctx.write_string(f, self.timecode_framerate)

        ctx.write_u8(f, 0x03)

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
        AVBPropertyDef('essence_element_size_kind',  'OMFI:DIDD:EssenceElementSizeKind',                 'uint8'),
        AVBPropertyDef('frame_checked_with_mapper',  'OMFI:DIDD:FrameSampleSizeHasBeenCheckedWithMapper', 'bool'),
    ]
    __slots__ = ()

    def read(self, f):
        super(DIDDescriptor, self).read(f)
        ctx = self.root.ictx
        ctx.read_assert_tag(f, 0x02)
        ctx.read_assert_tag(f, 0x02)

        self.stored_height = ctx.read_s32(f)
        self.stored_width  = ctx.read_s32(f)

        self.sampled_height = ctx.read_s32(f)
        self.sampled_width  = ctx.read_s32(f)

        self.sampled_x_offset = ctx.read_s32(f)
        self.sampled_y_offset = ctx.read_s32(f)

        self.display_height = ctx.read_s32(f)
        self.display_width  = ctx.read_s32(f)

        self.display_x_offset = ctx.read_s32(f)
        self.display_y_offset = ctx.read_s32(f)

        self.frame_layout = ctx.read_s16(f)

        numerator = ctx.read_s32(f)
        denominator = ctx.read_s32(f)
        self.aspect_ratio = [numerator, denominator]

        line_map_byte_size = ctx.read_s32(f)
        self.line_map = []
        if line_map_byte_size:
            for i in range(line_map_byte_size // 4):
                v = ctx.read_s32(f)
                self.line_map.append(v)

        self.alpha_transparency = ctx.read_s32(f)
        self.uniformness = ctx.read_bool(f)

        self.did_image_size = ctx.read_s32(f)

        self.next_did_desc = ctx.read_object_ref(self.root, f)

        self.compress_method = ctx.read_fourcc(f)

        self.resolution_id = ctx.read_s32(f)
        self.image_alignment_factor =  ctx.read_s32(f)

        for tag in ctx.iter_ext(f):
            if tag == 0x01:
                ctx.read_assert_tag(f, 69)
                self.frame_index_byte_order = ctx.read_s16(f)

            elif tag == 0x02:
                ctx.read_assert_tag(f, 71)
                self.frame_sample_size = ctx.read_s32(f)

            elif tag == 0x03:
                ctx.read_assert_tag(f, 71)
                self.first_frame_offset = ctx.read_s32(f)

            elif tag == 0x04:
                ctx.read_assert_tag(f, 71)
                self.client_fill_start = ctx.read_s32(f)

                ctx.read_assert_tag(f, 71)
                self.client_fill_end = ctx.read_s32(f)

            elif tag == 0x05:
                ctx.read_assert_tag(f, 71)
                self.offset_to_rle_frame_index = ctx.read_s32(f)

            elif tag == 0x06:
                ctx.read_assert_tag(f, 71)
                self.frame_start_offset = ctx.read_s32(f)

            elif tag == 0x08:
                # valid
                self.valid_box = []
                ctx.read_assert_tag(f, 71)
                x = ctx.read_s32(f)
                ctx.read_assert_tag(f, 71)
                y = ctx.read_s32(f)
                self.valid_box.append([x, y])

                ctx.read_assert_tag(f, 71)
                x = ctx.read_s32(f)
                ctx.read_assert_tag(f, 71)
                y = ctx.read_s32(f)
                self.valid_box.append([x, y])

                ctx.read_assert_tag(f, 71)
                x = ctx.read_s32(f)
                ctx.read_assert_tag(f, 71)
                y = ctx.read_s32(f)
                self.valid_box.append([x, y])

                ctx.read_assert_tag(f, 71)
                x = ctx.read_s32(f)
                ctx.read_assert_tag(f, 71)
                y = ctx.read_s32(f)
                self.valid_box.append([x, y])

                # essence
                self.essence_box = []
                ctx.read_assert_tag(f, 71)
                x = ctx.read_s32(f)
                ctx.read_assert_tag(f, 71)
                y = ctx.read_s32(f)
                self.essence_box.append([x, y])

                ctx.read_assert_tag(f, 71)
                x = ctx.read_s32(f)
                ctx.read_assert_tag(f, 71)
                y = ctx.read_s32(f)
                self.essence_box.append([x, y])

                ctx.read_assert_tag(f, 71)
                x = ctx.read_s32(f)
                ctx.read_assert_tag(f, 71)
                y = ctx.read_s32(f)
                self.essence_box.append([x, y])

                ctx.read_assert_tag(f, 71)
                x = ctx.read_s32(f)
                ctx.read_assert_tag(f, 71)
                y = ctx.read_s32(f)
                self.essence_box.append([x, y])

                # source
                self.source_box = []
                ctx.read_assert_tag(f, 71)
                x = ctx.read_s32(f)
                ctx.read_assert_tag(f, 71)
                y = ctx.read_s32(f)
                self.source_box.append([x, y])

                ctx.read_assert_tag(f, 71)
                x = ctx.read_s32(f)
                ctx.read_assert_tag(f, 71)
                y = ctx.read_s32(f)
                self.source_box.append([x, y])

                ctx.read_assert_tag(f, 71)
                x = ctx.read_s32(f)
                ctx.read_assert_tag(f, 71)
                y = ctx.read_s32(f)
                self.source_box.append([x, y])

                ctx.read_assert_tag(f, 71)
                x = ctx.read_s32(f)
                ctx.read_assert_tag(f, 71)
                y = ctx.read_s32(f)
                self.source_box.append([x, y])

            elif tag == 9:
                # print("\n??!", peek_data(f).encode('hex'), '\n')
                self.framing_box = []
                ctx.read_assert_tag(f, 71)
                x = ctx.read_s32(f)
                ctx.read_assert_tag(f, 71)
                y = ctx.read_s32(f)
                self.framing_box.append([x, y])

                ctx.read_assert_tag(f, 71)
                x = ctx.read_s32(f)
                ctx.read_assert_tag(f, 71)
                y = ctx.read_s32(f)
                self.framing_box.append([x, y])

                ctx.read_assert_tag(f, 71)
                x = ctx.read_s32(f)
                ctx.read_assert_tag(f, 71)
                y = ctx.read_s32(f)
                self.framing_box.append([x, y])

                ctx.read_assert_tag(f, 71)
                x = ctx.read_s32(f)
                ctx.read_assert_tag(f, 71)
                y = ctx.read_s32(f)
                self.framing_box.append([x, y])

                ctx.read_assert_tag(f, 71)
                self.reformatting_option = ctx.read_s32(f)

            elif tag == 10:
                ctx.read_assert_tag(f, 80)
                self.transfer_characteristic = ctx.read_raw_uuid(f)
            elif tag == 11:
                ctx.read_assert_tag(f, 80)
                self.color_primaries =  ctx.read_raw_uuid(f)
                ctx.read_assert_tag(f, 80)
                self.coding_equations = ctx.read_raw_uuid(f)
            elif tag == 12:
                ctx.read_assert_tag(f, 80)
                self.essence_compression = ctx.read_raw_uuid(f)
            elif tag == 14:
                ctx.read_assert_tag(f, 68)
                self.essence_element_size_kind = ctx.read_u8(f)
            elif tag == 15:
                ctx.read_assert_tag(f, 66)
                self.frame_checked_with_mapper = ctx.read_bool(f)

            else:
                raise ValueError("%s: unknown ext tag 0x%02X %d" % (str(self.class_id), tag,tag))

        if self.class_id[:] == b'DIDD':
            ctx.read_assert_tag(f, 0x03)

    def write(self, f):
        super(DIDDescriptor, self).write(f)
        ctx = self.root.octx
        ctx.write_u8(f, 0x02)
        ctx.write_u8(f, 0x02)

        ctx.write_s32(f, self.stored_height)
        ctx.write_s32(f, self.stored_width)

        ctx.write_s32(f, self.sampled_height)
        ctx.write_s32(f, self.sampled_width)

        ctx.write_s32(f, self.sampled_x_offset)
        ctx.write_s32(f, self.sampled_y_offset)

        ctx.write_s32(f, self.display_height)
        ctx.write_s32(f, self.display_width)

        ctx.write_s32(f, self.display_x_offset)
        ctx.write_s32(f, self.display_y_offset)

        ctx.write_s16(f, self.frame_layout)

        ctx.write_s32(f, self.aspect_ratio[0])
        ctx.write_s32(f, self.aspect_ratio[1])

        ctx.write_s32(f, len(self.line_map) * 4)
        for i in self.line_map:
            ctx.write_s32(f, i)


        ctx.write_s32(f, self.alpha_transparency)
        ctx.write_bool(f, self.uniformness)

        ctx.write_s32(f, self.did_image_size)

        ctx.write_object_ref(self.root, f, self.next_did_desc)

        assert len(self.compress_method) == 4
        ctx.write_fourcc(f, self.compress_method)

        ctx.write_s32(f, self.resolution_id)
        ctx.write_s32(f, self.image_alignment_factor)

        if hasattr(self, 'frame_index_byte_order'):
            ctx.write_u8(f, 0x01)
            ctx.write_u8(f, 0x01)
            ctx.write_u8(f, 69)
            ctx.write_s16(f, self.frame_index_byte_order)

        if hasattr(self, 'frame_sample_size'):
            ctx.write_u8(f, 0x01)
            ctx.write_u8(f, 0x02)
            ctx.write_u8(f, 71)
            ctx.write_s32(f, self.frame_sample_size)

        if hasattr(self, 'first_frame_offset'):
            ctx.write_u8(f, 0x01)
            ctx.write_u8(f, 0x03)
            ctx.write_u8(f, 71)
            ctx.write_s32(f, self.first_frame_offset)

        if hasattr(self, 'client_fill_start'):
            ctx.write_u8(f, 0x01)
            ctx.write_u8(f, 0x04)
            ctx.write_u8(f, 71)
            ctx.write_s32(f, self.client_fill_start)

            ctx.write_u8(f, 71)
            ctx.write_s32(f, self.client_fill_end)

        if hasattr(self, 'offset_to_rle_frame_index'):
            ctx.write_u8(f, 0x01)
            ctx.write_u8(f, 0x05)
            ctx.write_u8(f, 71)
            ctx.write_s32(f, self.offset_to_rle_frame_index)

        if hasattr(self, 'frame_start_offset'):
            ctx.write_u8(f, 0x01)
            ctx.write_u8(f, 0x06)
            ctx.write_u8(f, 71)
            ctx.write_s32(f, self.frame_start_offset)

        if hasattr(self, 'valid_box') and hasattr(self, 'essence_box') and hasattr(self, 'source_box'):
            ctx.write_u8(f, 0x01)
            ctx.write_u8(f, 0x08)

            ctx.write_u8(f, 71)
            ctx.write_s32(f, self.valid_box[0][0])
            ctx.write_u8(f, 71)
            ctx.write_s32(f, self.valid_box[0][1])

            ctx.write_u8(f, 71)
            ctx.write_s32(f, self.valid_box[1][0])
            ctx.write_u8(f, 71)
            ctx.write_s32(f, self.valid_box[1][1])

            ctx.write_u8(f, 71)
            ctx.write_s32(f, self.valid_box[2][0])
            ctx.write_u8(f, 71)
            ctx.write_s32(f, self.valid_box[2][1])

            ctx.write_u8(f, 71)
            ctx.write_s32(f, self.valid_box[3][0])
            ctx.write_u8(f, 71)
            ctx.write_s32(f, self.valid_box[3][1])

            # essence
            ctx.write_u8(f, 71)
            ctx.write_s32(f, self.essence_box[0][0])
            ctx.write_u8(f, 71)
            ctx.write_s32(f, self.essence_box[0][1])


            ctx.write_u8(f, 71)
            ctx.write_s32(f, self.essence_box[1][0])
            ctx.write_u8(f, 71)
            ctx.write_s32(f, self.essence_box[1][1])

            ctx.write_u8(f, 71)
            ctx.write_s32(f, self.essence_box[2][0])
            ctx.write_u8(f, 71)
            ctx.write_s32(f, self.essence_box[2][1])

            ctx.write_u8(f, 71)
            ctx.write_s32(f, self.essence_box[3][0])
            ctx.write_u8(f, 71)
            ctx.write_s32(f, self.essence_box[3][1])

            # source
            ctx.write_u8(f, 71)
            ctx.write_s32(f, self.source_box[0][0])
            ctx.write_u8(f, 71)
            ctx.write_s32(f, self.source_box[0][1])

            ctx.write_u8(f, 71)
            ctx.write_s32(f, self.source_box[1][0])
            ctx.write_u8(f, 71)
            ctx.write_s32(f, self.source_box[1][1])

            ctx.write_u8(f, 71)
            ctx.write_s32(f, self.source_box[2][0])
            ctx.write_u8(f, 71)
            ctx.write_s32(f, self.source_box[2][1])

            ctx.write_u8(f, 71)
            ctx.write_s32(f, self.source_box[3][0])
            ctx.write_u8(f, 71)
            ctx.write_s32(f, self.source_box[3][1])

        if hasattr(self, 'framing_box') and hasattr(self, 'reformatting_option'):
            ctx.write_u8(f, 0x01)
            ctx.write_u8(f, 9)

            # print("\n??!", peek_data(f).encode('hex'), '\n')
            ctx.write_u8(f, 71)
            ctx.write_s32(f, self.framing_box[0][0])
            ctx.write_u8(f, 71)
            ctx.write_s32(f, self.framing_box[0][1])

            ctx.write_u8(f, 71)
            ctx.write_s32(f, self.framing_box[1][0])
            ctx.write_u8(f, 71)
            ctx.write_s32(f, self.framing_box[1][1])

            ctx.write_u8(f, 71)
            ctx.write_s32(f, self.framing_box[2][0])
            ctx.write_u8(f, 71)
            ctx.write_s32(f, self.framing_box[2][1])

            ctx.write_u8(f, 71)
            ctx.write_s32(f, self.framing_box[3][0])
            ctx.write_u8(f, 71)
            ctx.write_s32(f, self.framing_box[3][1])

            ctx.write_u8(f, 71)
            ctx.write_s32(f, self.reformatting_option)

        if hasattr(self, 'transfer_characteristic'):
            ctx.write_u8(f, 0x01)
            ctx.write_u8(f, 10)
            ctx.write_u8(f, 80)
            ctx.write_raw_uuid(f, self.transfer_characteristic)

        if hasattr(self, 'color_primaries') and hasattr(self, 'coding_equations'):
            ctx.write_u8(f, 0x01)
            ctx.write_u8(f, 11)
            ctx.write_u8(f, 80)
            ctx.write_raw_uuid(f, self.color_primaries)
            ctx.write_u8(f, 80)
            ctx.write_raw_uuid(f, self.coding_equations)

        if hasattr(self, 'essence_compression'):
            ctx.write_u8(f, 0x01)
            ctx.write_u8(f, 12)
            ctx.write_u8(f, 80)
            ctx.write_raw_uuid(f, self.essence_compression)

        if hasattr(self, 'essence_element_size_kind'):
            ctx.write_u8(f, 0x01)
            ctx.write_u8(f, 14)
            ctx.write_u8(f, 68)
            ctx.write_u8(f, self.essence_element_size_kind)

        if hasattr(self, 'frame_checked_with_mapper'):
            ctx.write_u8(f, 0x01)
            ctx.write_u8(f, 15)
            ctx.write_u8(f, 66)
            ctx.write_bool(f, self.frame_checked_with_mapper)

        if self.class_id[:] == b'DIDD':
            ctx.write_u8(f, 0x03)

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
        ctx = self.root.ictx
        ctx.read_assert_tag(f, 0x02)
        ctx.read_assert_tag(f, 0x02)

        self.horizontal_subsampling = ctx.read_u32(f)
        self.vertical_subsampling = ctx.read_u32(f)
        self.component_width = ctx.read_s32(f)

        self.color_sitting = ctx.read_s16(f)
        self.black_ref_level = ctx.read_u32(f)
        self.white_ref_level = ctx.read_u32(f)
        self.color_range = ctx.read_u32(f)

        self.frame_index_offset = ctx.read_s64(f)

        for tag in ctx.iter_ext(f):
            if tag == 0x01:
                ctx.read_assert_tag(f, 72)
                self.alpha_sampled_width = ctx.read_u32(f)

            elif tag == 0x02:
                ctx.read_assert_tag(f, 72)
                self.ignore_bw = ctx.read_u32(f)
            else:
                raise ValueError("%s: unknown ext tag 0x%02X %d" % (str(self.class_id), tag,tag))

        if self.class_id[:] == b'CDCI':
            ctx.read_assert_tag(f, 0x03)

    def write(self, f):
        super(CDCIDescriptor, self).write(f)
        ctx = self.root.octx
        ctx.write_u8(f, 0x02)
        ctx.write_u8(f, 0x02)

        ctx.write_u32(f, self.horizontal_subsampling)
        ctx.write_u32(f, self.vertical_subsampling)
        ctx.write_s32(f, self.component_width)

        ctx.write_s16(f, self.color_sitting)
        ctx.write_u32(f, self.black_ref_level)
        ctx.write_u32(f, self.white_ref_level)
        ctx.write_u32(f, self.color_range)

        ctx.write_s64(f, self.frame_index_offset)

        if hasattr(self, 'alpha_sampled_width'):
            ctx.write_u8(f, 0x01)
            ctx.write_u8(f, 0x01)
            ctx.write_u8(f, 72)
            ctx.write_u32(f, self.alpha_sampled_width)

        if hasattr(self, 'ignore_bw'):
            ctx.write_u8(f, 0x01)
            ctx.write_u8(f, 0x02)
            ctx.write_u8(f, 72)
            ctx.write_u32(f, self.ignore_bw)

        if self.class_id[:] == b'CDCI':
            ctx.write_u8(f, 0x03)

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
        AVBPropertyDef('sequence_hdr',     "OMFI:MPGI:SequenceHdr",        "bytes"),
    ]
    __slots__ = ()

    def read(self, f):
        super(MPGIDescriptor, self).read(f)
        ctx = self.root.ictx
        ctx.read_assert_tag(f, 0x02)
        ctx.read_assert_tag(f, 0x01)

        self.mpeg_version = ctx.read_u8(f)
        self.profile = ctx.read_u8(f)
        self.gop_structure = ctx.read_u8(f)
        self.stream_type = ctx.read_u8(f)
        self.random_access = ctx.read_bool(f)
        self.leading_discard = ctx.read_bool(f)
        self.trailing_discard = ctx.read_bool(f)
        self.min_gop_length = ctx.read_u16(f)
        self.max_gop_length = ctx.read_u16(f)
        hdrlen = ctx.read_s32(f)
        assert hdrlen >= 0
        self.sequence_hdr = bytearray(f.read(hdrlen))

        ctx.read_assert_tag(f, 0x03)

    def write(self, f):
        super(MPGIDescriptor, self).write(f)
        ctx = self.root.octx
        ctx.write_u8(f, 0x02)
        ctx.write_u8(f, 0x01)

        ctx.write_u8(f, self.mpeg_version)
        ctx.write_u8(f, self.profile)
        ctx.write_u8(f, self.gop_structure)
        ctx.write_u8(f, self.stream_type)
        ctx.write_bool(f, self.random_access)
        ctx.write_bool(f, self.leading_discard)
        ctx.write_bool(f, self.trailing_discard)
        ctx.write_u16(f, self.min_gop_length)
        ctx.write_u16(f, self.max_gop_length)
        ctx.write_s32(f, len(self.sequence_hdr))
        f.write(self.sequence_hdr)

        ctx.write_u8(f, 0x03)

@utils.register_class
class JPEGDescriptor(CDCIDescriptor):
    class_id = b'JPED'
    propertydefs = CDCIDescriptor.propertydefs + [
        AVBPropertyDef('jpeg_table_id',           "OMFI:JPED:JPEGTableID",           "int32"),
        AVBPropertyDef('jpeg_frame_index_offset', "OMFI:JPED:OffsetToFrameIndexes",  "uint64"),
        AVBPropertyDef('quantization_tables',     "OMFI:JPED:QuantizationTables",    "bytes"),
        AVBPropertyDef('image_start_align',       "OMFI:JPED:ImageStartAlignment",   "int32"),
    ]
    __slots__ = ()

    def read(self, f):
        super(JPEGDescriptor, self).read(f)
        ctx = self.root.ictx
        ctx.read_assert_tag(f, 0x02)
        ctx.read_assert_tag(f, 0x01)

        self.jpeg_table_id = ctx.read_s32(f)
        self.jpeg_frame_index_offset = ctx.read_u64(f)
        table_size = ctx.read_s32(f)
        assert table_size >= 0
        self.quantization_tables = bytearray(f.read(table_size))

        for tag in ctx.iter_ext(f):
            if tag == 0x01:
                ctx.read_assert_tag(f, 71)
                self.image_start_align = ctx.read_s32(f)
            else:
                raise ValueError("unknown ext tag 0x%02X %d" % (tag,tag))

        ctx.read_assert_tag(f, 0x03)

    def write(self, f):
        super(JPEGDescriptor, self).write(f)
        ctx = self.root.octx
        ctx.write_u8(f, 0x02)
        ctx.write_u8(f, 0x01)

        ctx.write_s32(f, self.jpeg_table_id)
        ctx.write_u64(f, self.jpeg_frame_index_offset)
        ctx.write_s32(f, len(self.quantization_tables))
        f.write(self.quantization_tables)

        if hasattr(self, 'image_start_align'):
            ctx.write_u8(f, 0x01)
            ctx.write_u8(f, 0x01)
            ctx.write_u8(f, 71)
            ctx.write_s32(f, self.image_start_align)

        ctx.write_u8(f, 0x03)

def encode_pixel_layout(ctx, layout):
    pixel_layout = BytesIO()
    pixel_struct = BytesIO()

    for i in range(len(layout)):
        ctx.write_u8(pixel_layout, layout[i]['Code'])
        ctx.write_u8(pixel_struct, layout[i]['Size'])

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
        ctx = self.root.ictx
        ctx.read_assert_tag(f, 0x02)
        ctx.read_assert_tag(f, 0x01)

        # this seems to be encode the same way as in AAF
        layout_size = ctx.read_u32(f)
        pixel_layout = bytearray(f.read(layout_size))

        struct_size =  ctx.read_u32(f)
        pixel_struct = bytearray(f.read(struct_size))

        assert layout_size == struct_size

        layout = []
        for code, size in zip(pixel_layout, pixel_struct):
            layout.append({'Code': code, "Size" : size})

        self.pixel_layout = layout

        palette_layout_size = ctx.read_u32(f)
        assert palette_layout_size == 0

        palette_struct_size = ctx.read_u32(f)
        assert palette_struct_size == 0

        palette_size = ctx.read_u32(f)
        assert palette_size == 0

        for tag in ctx.iter_ext(f):
            if tag == 0x01:
                ctx.read_assert_tag(f, 77)
                self.frame_index_offset = ctx.read_u64(f)

            elif tag == 0x02:
                ctx.read_assert_tag(f, 66)
                self.has_comp_min_ref = ctx.read_bool(f)

                ctx.read_assert_tag(f, 72)
                self.comp_min_ref = ctx.read_u32(f)

                ctx.read_assert_tag(f, 66)
                self.has_comp_max_ref = ctx.read_bool(f)

                ctx.read_assert_tag(f, 72)
                self.comp_max_ref = ctx.read_u32(f)

            elif tag == 0x03:
                ctx.read_assert_tag(f, 72)
                self.alpha_min_ref = ctx.read_u32(f)

                ctx.read_assert_tag(f, 72)
                self.alpha_max_ref = ctx.read_u32(f)

            else:
                raise ValueError("unknown ext tag 0x%02X %d" % (tag,tag))

        ctx.read_assert_tag(f, 0x03)

    def write(self, f):
        super(RGBADescriptor, self).write(f)
        ctx = self.root.octx
        ctx.write_u8(f, 0x02)
        ctx.write_u8(f, 0x01)

        pixel_layout, pixel_struct = encode_pixel_layout(ctx, self.pixel_layout)

        # this seems to be encode the same way as in AAF
        ctx.write_u32(f, len(pixel_layout))
        f.write(pixel_layout)

        ctx.write_u32(f, len(pixel_struct))
        f.write(pixel_struct)

        # palette_layout_size
        ctx.write_u32(f, 0)
        # palette_struct_size
        ctx.write_u32(f, 0)
        # palette_size
        ctx.write_u32(f, 0)


        if hasattr(self, 'frame_index_offset'):
            ctx.write_u8(f, 0x01)
            ctx.write_u8(f, 0x01)
            ctx.write_u8(f, 77)
            ctx.write_u64(f, self.frame_index_offset)

        if hasattr(self, 'has_comp_min_ref'):
            ctx.write_u8(f, 0x01)
            ctx.write_u8(f, 0x02)
            ctx.write_u8(f, 66)
            ctx.write_bool(f, self.has_comp_min_ref)

            ctx.write_u8(f, 72)
            ctx.write_u32(f, self.comp_min_ref)

            ctx.write_u8(f, 66)
            ctx.write_bool(f, self.has_comp_max_ref)

            ctx.write_u8(f, 72)
            ctx.write_u32(f, self.comp_max_ref)

        if hasattr(self, 'alpha_min_ref'):
            ctx.write_u8(f, 0x01)
            ctx.write_u8(f, 0x03)
            ctx.write_u8(f, 72)
            ctx.write_u32(f, self.alpha_min_ref)

            ctx.write_u8(f, 72)
            ctx.write_u32(f, self.alpha_max_ref)

        ctx.write_u8(f, 0x03)
