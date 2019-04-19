from __future__ import (
    unicode_literals,
    absolute_import,
    print_function,
    division,
    )

import time
from datetime import datetime
from struct import (pack, unpack)
from uuid import UUID

from .utils import AVBObjectRef
from .mobid import MobID

exp10_pretty = {
5994: (59940, -3),
}

class AVBIOContext(object):
    def __init__(self, byte_order='little'):
        self.byte_order = byte_order

        if byte_order == 'little':
            self.read_u16  = self.read_u16le
            self.write_u16 = self.write_u16le
            self.read_s16  = self.read_s16le
            self.write_s16 = self.write_s16le
            self.read_u32  = self.read_u32le
            self.write_u32 = self.write_u32le
            self.read_s32  = self.read_s32le
            self.write_s32 = self.write_s32le
            self.read_u64  = self.read_u64le
            self.write_u64 = self.write_u64le
            self.read_s64  = self.read_s64le
            self.write_s64 = self.write_s64le

            self.read_double  = self.read_double_le
            self.write_double = self.write_double_le

            self.read_fourcc    = self.read_fourcc_le
            self.write_fourcc   = self.write_fourcc_le

        elif byte_order == 'big':
            self.read_u16  = self.read_u16be
            self.write_u16 = self.write_u16be
            self.read_s16  = self.read_s16be
            self.write_s16 = self.write_s16be
            self.read_u32  = self.read_u32be
            self.write_u32 = self.write_u32be
            self.read_s32  = self.read_s32be
            self.write_s32 = self.write_s32be
            self.read_u64  = self.read_u64be
            self.write_u64 = self.write_u64be
            self.read_s64  = self.read_s64be
            self.write_s64 = self.write_s64be

            self.read_double = self.read_double_be
            self.write_double = self.write_double_be

            self.read_fourcc    = self.read_fourcc_be
            self.write_fourcc   = self.write_fourcc_be
        else:
            raise ValueError('bytes_order must be "big" or "little"')

    @staticmethod
    def read_assert_tag(f, version):
        version_mark = AVBIOContext.read_u8(f)
        if version_mark != version:
            raise AssertionError("%d != %d" % (version_mark, version))

    @staticmethod
    def iter_ext(f):
        while True:
            pos = f.tell()
            tag = AVBIOContext.read_u8(f)
            if tag != 0x01:
                f.seek(pos)
                break

            tag = AVBIOContext.read_u8(f)
            yield tag

    @staticmethod
    def reverse_str(s):
        size = len(s)
        result = bytearray(size)
        for i in range(size):
            result[size - 1 - i] = s[i]

        return bytes(result)

    @staticmethod
    def datetime_to_timestamp(d):
        return int(time.mktime(d.timetuple()))

    @staticmethod
    def read_u8(f):
        (result, ) = unpack(b"B", f.read(1))
        return result

    @staticmethod
    def write_u8(f, value):
        f.write(pack(b"B", value))

    @staticmethod
    def read_s8(f):
        (result, ) = unpack(b"b", f.read(1))
        return result

    @staticmethod
    def write_s8(f, value):
        f.write(pack(b"b", value))

    @staticmethod
    def read_bool(f):
        return AVBIOContext.read_u8(f) == 0x01

    @staticmethod
    def write_bool(f, value):
        if value:
            AVBIOContext.write_u8(f, 0x01)
        else:
            AVBIOContext.write_u8(f, 0x00)

    # complex data types

    def read_exp10_encoded_float(self, f):
        mantissa = self.read_s32(f)
        exp10 = self.read_s16(f)

        return float(mantissa) * pow(10, exp10)

    def write_exp10_encoded_float(self, f, value):
        exponent = 0
        while int(value) != value:
            if abs(value * 10) >= 0x7FFFFFFF:
                break
            if exponent <= -6:
                break
            value *= 10
            exponent -= 1

        # remap values pretty values to match seen files
        if value in exp10_pretty:
            self.write_s32(f, exp10_pretty[value][0])
            self.write_s16(f, exp10_pretty[value][1])
        else:
            self.write_s32(f, int(value))
            self.write_s16(f, exponent)


    def read_string(self, f, encoding = 'macroman'):
        size = self.read_u16(f)
        if size >= 65535:
            return u""

        s = f.read(size)
        s = s.strip(b'\x00')
        return s.decode(encoding)

    def write_string(self, f, s, encoding = 'macroman'):
        s = s or b""
        if s == b"":
            self.write_u16(f, 0)
            return

        data = s.encode(encoding)
        if encoding == 'utf-8':
            data = b'\x00\x00' + data

        size = len(data)
        self.write_u16(f, size)
        f.write(data)

    def read_object_ref(self, root, f):
        index = self.read_u32(f)
        ref =  AVBObjectRef(root, index)
        if not root.check_refs or ref.valid:
            return ref
        raise ValueError("bad index: %d" % index)

    def write_object_ref(self, root, f, value):
        if value is None:
            index = 0
        elif root.debug_copy_refs:
            index = value.index
        elif value.instance_id not in root.ref_mapping:
            raise Exception("object not written yet")
        else:
            index = root.ref_mapping[value.instance_id]

        self.write_u32(f, index)

    def read_uuid(self, f):
        data = b''
        self.read_assert_tag(f, 72)
        data += f.read(4)

        self.read_assert_tag(f, 70)
        data += f.read(2)

        self.read_assert_tag(f, 70)
        data += f.read(2)

        self.read_assert_tag(f, 65)
        data4len = self.read_s32(f)
        assert data4len == 8
        data += f.read(8)

        if self.byte_order == 'little':
            return UUID(bytes_le=data)
        else:
            return UUID(bytes=data)

    def write_uuid(self, f, value):
        self.write_u8(f, 72)
        self.write_u32(f, value.time_low)
        self.write_u8(f, 70)
        self.write_u16(f, value.time_mid)
        self.write_u8(f, 70)
        self.write_u16(f, value.time_hi_version)

        self.write_u8(f, 65)
        self.write_s32(f, 8)
        if self.byte_order == 'little':
            f.write(value.bytes_le[8:])
        else:
            f.write(value.bytes[8:])

    def read_mob_id(self, f):
        m = MobID()
        self.read_assert_tag(f, 65)
        smpte_label_len = self.read_s32(f)
        assert smpte_label_len == 12

        m.SMPTELabel = [self.read_u8(f) for i in range(12)]

        self.read_assert_tag(f, 68)
        m.length = self.read_u8(f)

        self.read_assert_tag(f, 68)
        m.instanceHigh = self.read_u8(f)

        self.read_assert_tag(f, 68)
        m.instanceMid = self.read_u8(f)

        self.read_assert_tag(f, 68)
        m.instanceLow = self.read_u8(f)

        m.material = self.read_uuid(f)
        return m

    def write_mob_id(self, f, m):

        self.write_u8(f, 65)
        self.write_s32(f, 12)
        for i in m.SMPTELabel:
            self.write_u8(f, i)

        self.write_u8(f, 68)
        self.write_u8(f, m.length)

        self.write_u8(f, 68)
        self.write_u8(f, m.instanceHigh)

        self.write_u8(f, 68)
        self.write_u8(f, m.instanceMid)

        self.write_u8(f, 68)
        self.write_u8(f, m.instanceLow)

        self.write_uuid(f, m.material)

    def read_raw_uuid(self, f):
        if self.byte_order == 'little':
            return UUID(bytes_le=f.read(16))
        else:
            return UUID(bytes=f.read(16))

    def write_raw_uuid(self, f, value):
        if self.byte_order == 'little':
            f.write(value.bytes_le)
        else:
            f.write(value.bytes)

    def read_datetime(self, f):
        return datetime.fromtimestamp(self.read_u32(f))

    def write_datetime(self, f, value):
        self.write_u32(f, self.datetime_to_timestamp(value))

    def read_rect(self, f):
        version = self.read_s16(f)
        assert version == 1

        a = self.read_s16(f)
        b = self.read_s16(f)
        c = self.read_s16(f)
        d = self.read_s16(f)

        return [a,b,c,d]

    def write_rect(self, f, v):
        self.write_s16(f, 1)
        self.write_s16(f, v[0])
        self.write_s16(f, v[1])
        self.write_s16(f, v[2])
        self.write_s16(f, v[3])

    def read_rgb_color(self, f):
        version = self.read_s16(f)
        assert version == 1
        r = self.read_u16(f)
        g = self.read_u16(f)
        b = self.read_u16(f)

        return [r,g,b]

    def write_rgb_color(self, f, v):
        self.write_s16(f, 1)
        self.write_u16(f, v[0])
        self.write_u16(f, v[1])
        self.write_u16(f, v[2])

    # little

    @staticmethod
    def read_u16le(f):
        (result, ) = unpack(b"<H", f.read(2))
        return result

    @staticmethod
    def write_u16le(f, value):
        f.write(pack(b"<H", value))

    @staticmethod
    def read_s16le(f):
        (result, ) = unpack(b"<h", f.read(2))
        return result

    @staticmethod
    def write_s16le(f, value):
        f.write(pack(b"<h", value))

    @staticmethod
    def read_u32le(f):
        (result, ) = unpack(b"<I", f.read(4))
        return result

    @staticmethod
    def write_u32le(f, value):
        return f.write(pack(b"<I", value))

    @staticmethod
    def read_s32le(f):
        (result, ) = unpack(b"<i", f.read(4))
        return result

    @staticmethod
    def write_s32le(f, value):
        return f.write(pack(b"<i", value))

    @staticmethod
    def read_u64le(f):
        return unpack(b"<Q", f.read(8))[0]

    @staticmethod
    def write_u64le(f, value):
        return f.write(pack(b"<Q", value))

    @staticmethod
    def read_s64le(f):
        return unpack(b"<q", f.read(8))[0]

    @staticmethod
    def write_s64le(f, value):
        return f.write(pack(b"<q", value))

    @staticmethod
    def read_double_le(f):
        return unpack(b"<d", f.read(8))[0]

    @staticmethod
    def write_double_le(f, value):
        f.write(pack(b"<d", value))

    @staticmethod
    def read_fourcc_le(f):
        return f.read(4)[::-1]

    @staticmethod
    def write_fourcc_le(f, value):
        assert len(value) == 4
        f.write(AVBIOContext.reverse_str(value))

    # big

    @staticmethod
    def read_u16be(f):
        (result, ) = unpack(b">H", f.read(2))
        return result

    @staticmethod
    def write_u16be(f, value):
        f.write(pack(b">H", value))

    @staticmethod
    def read_s16be(f):
        (result, ) = unpack(b">h", f.read(2))
        return result

    @staticmethod
    def write_s16be(f, value):
        f.write(pack(b">h", value))

    @staticmethod
    def read_u32be(f):
        (result, ) = unpack(b">I", f.read(4))
        return result

    @staticmethod
    def write_u32be(f, value):
        return f.write(pack(b">I", value))

    @staticmethod
    def read_s32be(f):
        (result, ) = unpack(b">i", f.read(4))
        return result

    @staticmethod
    def write_s32be(f, value):
        return f.write(pack(b">i", value))

    @staticmethod
    def read_u64be(f):
        return unpack(b">Q", f.read(8))[0]

    @staticmethod
    def write_u64be(f, value):
        return f.write(pack(b">Q", value))

    @staticmethod
    def read_s64be(f):
        return unpack(b">q", f.read(8))[0]

    @staticmethod
    def write_s64be(f, value):
        return f.write(pack(b">q", value))

    @staticmethod
    def read_double_be(f):
        return unpack(b"<d", f.read(8))[0]

    @staticmethod
    def write_double_be(f, value):
        f.write(pack(b"<d", value))

    @staticmethod
    def read_fourcc_be(f):
        return f.read(4)

    @staticmethod
    def write_fourcc_be(f, value):
        assert len(value) == 4
        f.write(value)
