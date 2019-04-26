from __future__ import (
    unicode_literals,
    absolute_import,
    print_function,
    division,
)

import struct
from io import BytesIO
import os
from uuid import UUID, uuid4
from binascii import hexlify, unhexlify

class AVBObjectRef(object):
    __slots__ = ('root', 'index')
    def __init__(self, root, index):
        self.root = root
        self.index = index

    @property
    def value(self):
        if self.index <= 0:
            return None
        if self.root.debug_copy_refs:
            return self

        return self.root.read_object(self.index)

    @property
    def class_id(self):
        if not self.root.check_refs:
            return b'NULL'
        if self.valid:
            chunk = self.root.read_chunk(self.index)
            return chunk.class_id

    @property
    def valid(self):
        if self.index >= len(self.root.object_positions):
            return False
        return True

    def __repr__(self):
        s = "%s.%s"  % (self.__class__.__module__,
                                self.__class__.__name__)
        if self.root and self.index and self.valid:
            chunk = self.root.read_chunk(self.index)
            s += " %s idx: %d pos: %d" % (chunk.class_id, self.index, chunk.pos)
        return '<%s at 0x%x>' % (s, id(self))

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

def peek_data(f, size=None):
    pos = f.tell()
    if size:
        data = f.read(size)
    else:
        data = f.read()
    f.seek(pos)
    return data

def unpack_u16le_from(buffer, offset):
    value  = buffer[offset]
    value += buffer[offset+1] << 8
    return value

def unpack_u32le_from(buffer, offset):
    value  = buffer[offset]
    value += buffer[offset+1] << 8
    value += buffer[offset+2] << 16
    value += buffer[offset+3] << 24
    return value

def generate_uid():
    v = uuid4().int & (1<<64)-1
    return v

AVBClaseID_dict = {}
AVBClassName_dict = {}
def register_class(classobj):
    AVBClaseID_dict[classobj.class_id] = classobj
    AVBClassName_dict[classobj.__name__] = classobj

    for pdef in classobj.propertydefs:
        classobj.propertydefs_dict[pdef.name] = pdef

    return classobj

def register_helper_class(classobj):
    AVBClassName_dict[classobj.__name__] = classobj
    for pdef in classobj.propertydefs:
        classobj.propertydefs_dict[pdef.name] = pdef
    return classobj
