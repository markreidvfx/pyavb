from __future__ import (
    unicode_literals,
    absolute_import,
    print_function,
    division,
    )

import io
import os

from . attributes import read_attributes
from . import utils
from .utils import (
    read_string,
    read_u32le,
    read_fourcc,
    read_byte
)


class AVBChunk(object):
    def __init__(self, root, class_id, pos, size):
        self.root = root
        self.class_id = class_id
        self.pos = pos
        self.size = size

    def read(self):
        self.root.f.seek(self.pos)
        return self.root.f.read(self.size)

class AVBFile(object):
    def __init__(self, path, mode='r'):
        if mode in ('r', 'rb'):
            mode = 'rb'
        else:
            raise ValueError("invalid mode: %s" % mode)

        self.mode = mode
        self.f = io.open(path, self.mode)

        f = self.f
        file_bytes = f.read(2)
        if file_bytes != utils.MAC_BYTES:
            raise ValueError("Only Mac bytes supported")

        header = f.read(len(utils.MAGIC))
        if header != utils.MAGIC:
            raise ValueError("not avb file")

        pos = f.tell()

        assert read_fourcc(f) == 'OBJD'
        assert read_string(f) == 'AObjDoc'
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

        self.chunks = [AVBChunk(self, 'OBJD', pos, f.tell() - pos)]

        for i in range(num_objects):
            class_id = read_fourcc(f)
            size = read_u32le(f)
            pos = f.tell()

            self.chunks.append(AVBChunk(self, class_id, pos, size))

            # self.object_refs.append([object_id, object_pos, object_size])
            f.seek(size, os.SEEK_CUR)

        self.content = self.read_object(self.root_index)

    def read_object(self, index):
        if index == 0:
            return None

        chunk = self.chunks[index]
        data = chunk.read()

        if chunk.class_id == "ATTR":
            return read_attributes(self, io.BytesIO(data))

        obj_class = utils.AVBClaseID_dict.get(chunk.class_id, None)
        if obj_class:
            object_instance = obj_class(self)
            try:
                object_instance.read(io.BytesIO(data))
                return object_instance
            except:
                print(chunk.class_id)
                print(data.encode('hex'))
                print([data])
                raise

        else:
            raise NotImplementedError(chunk.class_id)


    def close(self):
        self.f.close()

    def __exit__(self, exc_type, exc_value, traceback):
        if (exc_type is None and exc_value is None and traceback is None):
            self.close()

    def __enter__(self):
        return self
