from __future__ import (
    unicode_literals,
    absolute_import,
    print_function,
    division,
    )

import time
from datetime import datetime
from struct import (pack, unpack)
from .utils import AVBObjectRef

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
            self.read_double  = self.read_doublele
            self.write_double = self.write_doublele

            self.read_fourcc    = self.read_fourcc_le
            self.write_fourcc   = self.write_fourcc_le
            self.read_string    = self.read_string_le
            self.write_string   = self.write_string_le
            self.read_datetime  = self.read_datetime_le
            self.write_datetime = self.write_datetime_le

            self.read_object_ref = self.read_object_ref_le
            self.write_object_ref = self.write_object_ref_le

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
            self.read_double = self.read_doublebe
            self.write_double = self.write_doublebe

            self.read_fourcc = self.read_fourcc_be
        else:
            raise ValueError('bytes_order must be "big" or "little"')

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
        return unpack(b"B", f.read(1))[0]

    @staticmethod
    def write_u8(f, value):
        f.write(pack(b"B", value))

    @staticmethod
    def read_s8(f):
        return unpack(b"b", f.read(1))[0]

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

    # little

    @staticmethod
    def read_u16le(f):
        return unpack(b"<H", f.read(2))[0]

    @staticmethod
    def write_u16le(f, value):
        f.write(pack(b"<H", value))

    @staticmethod
    def read_s16le(f):
        return unpack(b"<h", f.read(2))[0]

    @staticmethod
    def write_s16le(f, value):
        f.write(pack(b"<h", value))

    @staticmethod
    def read_u32le(f):
        return unpack(b"<I", f.read(4))[0]

    @staticmethod
    def write_u32le(f, value):
        return f.write(pack(b"<I", value))

    @staticmethod
    def read_s32le(f):
        return unpack(b"<i", f.read(4))[0]

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
    def read_doublele(f):
        return struct.unpack(b"<d", f.read(8))[0]

    @staticmethod
    def write_doublele(f, value):
        f.write(struct.pack(b"<d", value))

    @staticmethod
    def read_fourcc_le(f):
        return AVBIOContext.reverse_str(f.read(4))

    @staticmethod
    def write_fourcc_le(f, value):
        assert len(value) == 4
        f.write(AVBIOContext.reverse_str(value))

    @staticmethod
    def read_string_le(f, encoding = 'macroman'):
        size = AVBIOContext.read_u16le(f)
        if size >= 65535:
            return u""

        s = f.read(size)
        s = s.strip(b'\x00')
        return s.decode(encoding)

    @staticmethod
    def write_string_le(f, s, encoding = 'macroman'):
        s = s or b""
        if s == b"":
            AVBIOContext.write_u16le(f, 0)
            return

        data = s.encode(encoding)
        if encoding == 'utf-8':
            data = b'\x00\x00' + data

        size = len(data)
        AVBIOContext.write_u16le(f, size)
        f.write(data)

    @staticmethod
    def read_datetime_le(f):
        return datetime.fromtimestamp(AVBIOContext.read_u32le(f))

    @staticmethod
    def write_datetime_le(f, value):
        AVBIOContext.write_u32le(f, AVBIOContext.datetime_to_timestamp(value))

    @staticmethod
    def read_object_ref_le(root, f):
        index = AVBIOContext.read_u32le(f)
        ref =  AVBObjectRef(root, index)
        if not root.check_refs or ref.valid:
            return ref
        raise ValueError("bad index: %d" % index)

    @staticmethod
    def write_object_ref_le(root, f, value):
        if value is None:
            index = 0
        elif root.debug_copy_refs:
            index = value.index
        elif value.instance_id not in root.ref_mapping:
            raise Exception("object not written yet")
        else:
            index = root.ref_mapping[value.instance_id]

        AVBIOContext.write_u32le(f, index)

    # big

    @staticmethod
    def read_u16be(f):
        return unpack(b">H", f.read(2))[0]

    @staticmethod
    def write_u16be(f, value):
        f.write(pack(b">H", value))

    @staticmethod
    def read_s16be(f):
        return unpack(b">h", f.read(2))[0]

    @staticmethod
    def write_s16be(f, value):
        f.write(pack(b">h", value))

    @staticmethod
    def read_u32be(f):
        return unpack(b">I", f.read(4))[0]

    @staticmethod
    def write_u32be(f, value):
        return f.write(pack(b">I", value))

    @staticmethod
    def read_s32be(f):
        return unpack(b">i", f.read(4))[0]

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
    def read_doublebe(f):
        return struct.unpack(b"<d", f.read(8))[0]

    @staticmethod
    def write_doublebe(f, value):
        f.write(struct.pack(b"<d", value))
