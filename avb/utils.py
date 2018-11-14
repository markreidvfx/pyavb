from __future__ import (
    unicode_literals,
    absolute_import,
    print_function,
    division,
)

import struct
from io import BytesIO
import os

from uuid import UUID
from datetime import datetime

MAGIC=b'Domain'

MAC_BYTES =  b'\x06\x00'
PC_BYTES  =  b'\x00\x06'

MODE_PC  = 1
MODE_MAC = 0

class AVBObjectRef(object):
    def __init__(self, root, index):
        self.root = root
        self.index = index

    @property
    def value(self):
        if self.index <= 0:
            return None

        return self.root.read_object(self.index)

    @property
    def class_id(self):
        if self.valid:
            chunk = self.root.chunks[self.index]
            return chunk.class_id

    @property
    def valid(self):
        if self.index >= len(self.root.chunks):
            return False
        return True

    def __repr__(self):
        s = "%s.%s"  % (self.__class__.__module__,
                                self.__class__.__name__)
        if self.index and self.valid:
            chunk = self.root.chunks[self.index]
            s += " %s idx: %d pos: %d" % (chunk.class_id, self.index, chunk.pos)
        return '<%s at 0x%x>' % (s, id(self))

def reverse_str(s):
    result = b""
    for c in reversed(s):
        result += c

    return result

def read_s32le(f):
    return struct.unpack("<i", f.read(4))[0]

def read_u32le(f):
    return struct.unpack("<I", f.read(4))[0]

def read_s16le(f):
    return struct.unpack("<h", f.read(2))[0]

def read_u16le(f):
    return struct.unpack("<H", f.read(2))[0]

def read_byte(f):
    return struct.unpack("<B", f.read(1))[0]

def read_s8(f):
    return struct.unpack("<b", f.read(1))[0]

def read_s64le(f):
    return struct.unpack("<q", f.read(8))[0]

def read_u64le(f):
    return struct.unpack("<Q", f.read(8))[0]

def read_bool(f):
    return read_byte(f) == b'\x00'

def read_fourcc(f):
    return reverse_str(f.read(4))

def read_string(f, encoding = 'macroman'):
    size = read_u16le(f)
    if size >= 65535:
        return ""

    return f.read(size).decode(encoding)

def read_datetime(f):
    return datetime.utcfromtimestamp(read_u32le(f))

def read_raw_uuid(f):
    Data1 = reverse_str(f.read(4)).encode('hex')
    Data2 = reverse_str(f.read(2)).encode('hex')
    Data3 = reverse_str(f.read(2)).encode('hex')
    Data4 = f.read(8).encode('hex')
    data =  Data1 + Data2 + Data3 + Data4
    return UUID(data)

def read_uuid(f):
    tag = read_byte(f)
    assert tag == 72
    Data1 = reverse_str(f.read(4)).encode('hex')

    tag = read_byte(f)
    assert tag == 70
    Data2 = reverse_str(f.read(2)).encode('hex')

    tag = read_byte(f)
    assert tag == 70
    Data3 = reverse_str(f.read(2)).encode('hex')

    tag = read_byte(f)
    assert tag == 65
    data4len = read_s32le(f)
    assert data4len == 8
    Data4 = b""
    for i in range(8):
        Data4 += b"%02X" % read_byte(f)

    data =  Data1 + Data2 + Data3 + Data4
    return UUID(data)

def int_from_bytes(data, byte_order='big'):
    num = 0
    if byte_order == 'little':
        for i, byte in enumerate(data):
            num += byte << (i * 8)
        return num
    elif byte_order == 'big':
        length = len(data) - 1
        for i, byte in enumerate(data):
            num += byte << ((length-i) * 8)
        return num
    else:
        raise ValueError('endianess must be "little" or "big"')

def bytes_from_int(num, length, byte_order='big'):
    if byte_order == 'little':
        v = bytearray((num >> (i * 8) & 0xff for i in range(length)))
        return bytes(v)
    elif byte_order == 'big':
        v = bytearray((num >> (length - 1 - i) * 8) & 0xff for i in range(length))
        return bytes(v)
    else:
        raise ValueError('endianess must be "little" or "big"')

def read_object_ref(root, f):
    index = read_u32le(f)
    ref =  AVBObjectRef(root, index)
    if ref.valid:
        return ref
    raise ValueError("bad index: %d" % index)

def read_exp10_encoded_float(f):
    mantissa = read_s32le(f)
    exp10 = read_s16le(f)

    return float(mantissa) * pow(10, exp10)

def read_rect(f):
    version = read_s16le(f)
    assert version == 1

    a = read_s16le(f)
    b = read_s16le(f)
    c = read_s16le(f)
    d = read_s16le(f)

    return [a,b,c,d]

def read_rgb_color(f):
    version = read_s16le(f)
    assert version == 1
    r = read_u16le(f)
    g = read_u16le(f)
    b = read_u16le(f)

    return [r,g,b]

def peek_data(f, size=None):
    pos = f.tell()
    if size:
        data = f.read(size)
    else:
        data = f.read()
    f.seek(pos)
    return data

AVBClaseID_dict = {}
AVBClassName_dict = {}
def register_class(classobj):
    AVBClaseID_dict[classobj.class_id] = classobj
    AVBClassName_dict[classobj.__name__] = classobj

    return classobj
