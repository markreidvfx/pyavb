from __future__ import (
    unicode_literals,
    absolute_import,
    print_function,
    division,
    )

import datetime

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
    read_string, write_string,
    read_u32le, write_u32le, write_u16le,
    read_fourcc, write_fourcc,
    read_u8, write_u8,
    reverse_str,
)
from .core import walk_references


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
        size =struct.pack(b"<I", self.size)
        data =  header + size + self.read()
        return binascii.hexlify(data)

def read_chunk(root, f):
    class_id = read_fourcc(f)
    size = read_u32le(f)
    pos = f.tell()

    return AVBChunk(root, class_id, pos, size)

class AVBFactory(object):

    def __init__(self, root):
        self.root = root
        self.class_name = None

    def __getattr__(self, name):
        self.class_name = name
        return self.create_instance

    def from_name(self, name, *args, **kwargs):

        classobj = obj_class = utils.AVBClassName_dict.get(name, None)

        # obj = classobj(None, *args, **kwargs)
        obj = classobj.__new__(classobj)
        obj.root = self.root
        if hasattr(obj, 'class_id'):
            self.root.next_object_id += 1
            obj.instance_id = self.root.next_object_id

            self.root.modified_objects[obj.instance_id] = obj
            self.root.object_cache[obj.instance_id] = obj

        obj.__init__(*args, **kwargs)

        return obj

    def create_instance(self, *args, **kwargs):
        return self.from_name(self.class_name, *args, **kwargs)

class AVBFile(object):
    def __init__(self, path=None, buffering=io.DEFAULT_BUFFER_SIZE):

        self.check_refs = True
        self.debug_copy_refs = False
        self.reading = False

        self.create = AVBFactory(self)
        self.object_cache = WeakValueDictionary()
        self.modified_objects = {}
        self.next_object_id = 0

        if path is None:
            self.setup_empty()
            return

        self.f = io.open(path, 'rb', buffering=buffering)

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
        assert read_u8(f) == 0x04

        self.last_save = read_string(f)
        num_objects = read_u32le(f)
        self.root_index = read_u32le(f)

        assert read_u32le(f) == 0x49494949

        self.last_save_timestamp = read_u32le(f)

        # skip 4 bytes
        f.read(4)

        assert read_fourcc(f) == b'ATob'
        assert read_fourcc(f) == b'ATve'

        self.creator_version = read_string(f)

        # Reserved data
        f.read(16)

        self.root_chunk = AVBChunk(self, b'OBJD', pos, f.tell() - pos)

        self.object_positions = array.array(str('L'), [0 for i in range(num_objects+1)])
        self.next_object_id = len(self.object_positions)

        for i in range(num_objects):
            self.object_positions[i+1] = f.tell()
            class_id = read_fourcc(f)
            size = read_u32le(f)

            f.seek(size, os.SEEK_CUR)

        self.content = self.read_object(self.root_index)

    def setup_empty(self):
        self.f = None

        self.creator_version = u'pyavb 0.1.0'
        self.content = self.create.Bin()

        self.update_save_time()

    def update_save_time(self):
        # TODO: Verify what type of timestamps are used
        now = datetime.datetime.now()
        self.last_save = now.strftime(u'%Y/%m/%d %H:%M:%S')
        self.last_save_timestamp = utils.datetime_to_timestamp(now)

    def add_modified(self, obj):
        self.modified_objects[obj.instance_id] = obj

    def write_header(self, f):
        f.write(utils.MAC_BYTES)
        f.write(utils.MAGIC)

        write_fourcc(f, b'OBJD')
        write_string(f, u'AObjDoc')
        write_u8(f, 0x04)
        write_string(f, self.last_save)
        pos = f.tell()
        write_u32le(f, 0)
        write_u32le(f, 0)
        write_u32le(f, 0x49494949)
        write_u32le(f, self.last_save_timestamp)
        write_u32le(f, 0)

        write_fourcc(f, b'ATob')
        write_fourcc(f, b'ATve')

        # version =

        s = f.tell()
        v = self.creator_version.encode('macroman')
        v = v[:30]
        write_u16le(f, 30)
        f.write(v)

        # pad with 0x20
        while f.tell() - s < 32:
            write_u8(f, 0x20)
        f.write(bytearray(16))

        return pos

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
            try:
                self.reading = True
                # NOTE: objects read from file do not run __init__
                object_instance = obj_class.__new__(obj_class, root=self)

                # Only OrderedDict needs run __init__ in order to work
                if chunk.class_id == b'ATTR':
                    object_instance.__init__(object_instance)

                r = io.BytesIO(data)
                object_instance.read(r)
                # print(len(r.read()))
                assert len(r.read()) == 0
                self.object_cache[index] = object_instance
                object_instance.instance_id = index
                return object_instance
            except:
                print(chunk.class_id)
                print(chunk.hex())
                print(traceback.format_exc())
                raise
            finally:
                self.reading = False

        else:
            print(chunk.class_id)
            print(chunk.hex())
            raise NotImplementedError(chunk.class_id)

    def write_object(self, f, obj):
        buffer = io.BytesIO()
        obj.write(buffer)
        data = buffer.getvalue()
        assert data[-1:] == b'\x03'

        write_fourcc(f, obj.class_id)
        write_u32le(f, len(data))
        f.write(data)

        # chunk = self.read_chunk(obj.instance_id)
        # orig_chunk_data = chunk.read()

        # if len(orig_chunk_data) != len(data):# or orig_chunk_data != data:
        #     print(obj, len(orig_chunk_data), len(data) )
        #     print(binascii.hexlify(orig_chunk_data))
        #     print("")
        #     print(binascii.hexlify(data))
        #     raise Exception()

    def write(self, path):
        self.next_chunk_id = 0
        self.ref_mapping = {}

        with io.open(path, 'wb') as f:
            count_pos = self.write_header(f)
            for obj in walk_references(self.content):
                if obj.instance_id in self.ref_mapping:
                    continue

                self.next_chunk_id += 1
                self.ref_mapping[obj.instance_id] = self.next_chunk_id
                self.write_object(f, obj)

            pos = f.tell()
            f.seek(count_pos)
            write_u32le(f, self.next_chunk_id)
            write_u32le(f, self.next_chunk_id)
            f.seek(pos)

    def chunks(self):
        for i in range(len(self.object_positions)):
            yield self.read_chunk(i)

    def iter_class_ids(self, class_id_list):
        for i, chunk in enumerate(self.chunks()):
            if chunk.class_id in class_id_list:
                yield self.read_object(i)

    def close(self):
        if self.f:
            self.f.close()

    def __exit__(self, exc_type, exc_value, traceback):
        if (exc_type is None and exc_value is None and traceback is None):
            self.close()

    def __enter__(self):
        return self
