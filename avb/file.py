from __future__ import (
    unicode_literals,
    absolute_import,
    print_function,
    division,
    )

import struct
import io
import os
import binascii
import traceback
import array
from weakref import WeakValueDictionary

# from . attributes import read_attributes
from . import utils
from .utils import (
    read_string,
    read_u32le,
    read_fourcc,
    read_byte,
    reverse_str,
)


class AVBChunk(object):
    __slots__ = ('root', 'class_id', 'pos', 'size')
    def __init__(self, root, class_id, pos, size):
        self.root = root
        self.class_id = class_id
        self.pos = pos
        self.size = size

    def read(self):
        self.root.f.seek(self.pos)
        return self.root.f.read(self.size)

    def hex(self):
        header = reverse_str(self.class_id)
        size =struct.pack("<I", self.size)
        data =  header + size + self.read()
        return binascii.hexlify(data)

def read_chunk(root, f):
    class_id = read_fourcc(f)
    size = read_u32le(f)
    pos = f.tell()

    return AVBChunk(root, class_id, pos, size)

class AVBFile(object):
    def __init__(self, path, mode='r', buffering=io.DEFAULT_BUFFER_SIZE):
        if mode in ('r', 'rb'):
            mode = 'rb'
        else:
            raise ValueError("invalid mode: %s" % mode)

        self.mode = mode
        self.check_refs = True
        self.f = io.open(path, self.mode, buffering=buffering)

        f = self.f
        file_bytes = f.read(2)
        if file_bytes != utils.MAC_BYTES:
            raise ValueError("Only Mac bytes supported")

        header = f.read(len(utils.MAGIC))
        if header != utils.MAGIC:
            raise ValueError("not avb file")

        pos = f.tell()

        assert read_fourcc(f) == b'OBJD'
        assert read_string(f) == u'AObjDoc'
        assert read_byte(f) == 0x04

        self.last_save = read_string(f)
        num_objects = read_u32le(f)
        self.root_index = read_u32le(f)

        assert read_u32le(f) == 0x49494949

        self.last_save_timestamp = read_u32le(f)

        # skip 4 bytes
        f.read(4)

        file_type = read_fourcc(f)
        creator = read_fourcc(f)
        # print(file_type, creator)

        self.creator_version = read_string(f)

        # Reserved data
        f.read(16)

        self.root_chunk = AVBChunk(self, b'OBJD', pos, f.tell() - pos)

        self.object_cache = WeakValueDictionary()
        self.object_positions = array.array(str('L'), [0 for i in range(num_objects+1)])

        for i in range(num_objects):
            self.object_positions[i+1] = f.tell()
            class_id = read_fourcc(f)
            size = read_u32le(f)

            f.seek(size, os.SEEK_CUR)

        self.content = self.read_object(self.root_index)

    def read_chunk(self, index):
        if index == 0:
            return self.root_chunk

        object_pos = self.object_positions[index]

        f = self.f
        f.seek(object_pos)
        class_id = read_fourcc(f)
        size = read_u32le(f)
        pos = f.tell()

        chunk = AVBChunk(self, class_id, pos, size)
        return chunk

    def read_object(self, index):
        if index == 0:
            return None

        object_instance = self.object_cache.get(index, None)
        if object_instance is not None:
            return object_instance

        chunk = self.read_chunk(index)
        data = chunk.read()

        obj_class = utils.AVBClaseID_dict.get(chunk.class_id, None)
        if obj_class:
            object_instance = obj_class(self)
            try:
                object_instance.read(io.BytesIO(data))
                self.object_cache[index] = object_instance
                return object_instance
            except:
                print(chunk.class_id)
                print(chunk.hex())
                print(traceback.format_exc())
                raise

        else:
            print(chunk.class_id)
            print(chunk.hex())
            raise NotImplementedError(chunk.class_id)

    def chunks(self):
        for i in range(len(self.object_positions)):
            yield self.read_chunk(i)

    def iter_class_ids(self, class_id_list):
        for i, chunk in enumerate(self.chunks()):
            if chunk.class_id in class_id_list:
                yield self.read_object(i)

    def close(self):
        self.f.close()

    def __exit__(self, exc_type, exc_value, traceback):
        if (exc_type is None and exc_value is None and traceback is None):
            self.close()

    def __enter__(self):
        return self
