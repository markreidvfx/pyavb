from __future__ import (
    unicode_literals,
    absolute_import,
    print_function,
    division,
    )
import uuid
from . import utils
from . import core
from .core import AVBPropertyDef, AVBPropertyData, AVBRefList

from . utils import (
    read_u8,    write_u8,
    read_s16le, write_s16le,
    read_u32le, write_u32le,
    read_s32le, write_s32le,
    read_string, write_string,
    read_object_ref, write_object_ref,
    read_assert_tag,
    peek_data,
)

INT_ATTR  = 1
STR_ATTR  = 2
OBJ_ATTR  = 3
BOB_ATTR  = 4

if bytes is not str:
    unicode = str

@utils.register_class
class Attributes(AVBPropertyData):
    class_id = b'ATTR'
    __slots__ = ('root', 'instance_id', '__weakref__')

    def __init__(self, root):
        super(Attributes, self).__init__()
        self.root = root
        self.instance_id  = uuid.uuid4()

    def read(self, f):
        read_assert_tag(f, 0x02)
        read_assert_tag(f, 0x01)

        count = read_u32le(f)
        result = {}

        for i in range(count):
            attr_type = read_u32le(f)
            attr_name = read_string(f)

            if attr_type == INT_ATTR:
                result[attr_name] = read_s32le(f)
            elif attr_type == STR_ATTR:
                result[attr_name] = read_string(f)
            elif attr_type == OBJ_ATTR:
                result[attr_name] = read_object_ref(self.root, f)
            elif attr_type == BOB_ATTR:
                size = read_u32le(f)
                result[attr_name] = bytearray(f.read(size))
            else:
                raise Exception("Unkown attr name: %s type: %d" % ( attr_name, attr_type))

        # print("read", result)
        self.update(result)
        read_assert_tag(f, 0x03)

    def write(self, f):
        write_u8(f, 0x02)
        write_u8(f, 0x01)

        write_u32le(f, len(self))
        for key, value in sorted(self.items()):
            assert isinstance(key, unicode)

            if isinstance(value, int):
                attr_type = INT_ATTR
            elif isinstance(value, unicode):
                attr_type = STR_ATTR
            elif isinstance(value, bytearray):
                attr_type = BOB_ATTR
            elif isinstance(value, bytes):
                raise ValueError("%s: bytes value type too ambiguous, use bytearray or unicode str" % key)
            else:
                # assume its AVBObject for now and hope for the best :p
                attr_type = OBJ_ATTR

            write_u32le(f, attr_type)
            write_string(f, key)

            if attr_type == INT_ATTR:
                write_s32le(f, value)
            elif attr_type == STR_ATTR:
                write_string(f, value)
            elif attr_type == OBJ_ATTR:
                write_object_ref(self.root, f, value)
            elif attr_type == BOB_ATTR:
                write_u32le(f, len(value))
                f.write(value)

        write_u8(f, 0x03)

@utils.register_class
class ParameterList(AVBRefList):
    class_id = b'PRLS'
    __slots__ = ()
    def read(self, f):
        read_assert_tag(f, 0x02)
        read_assert_tag(f, 0x01)

        count = read_s32le(f)
        for i in range(count):
            ref = read_object_ref(self.root, f)
            self.append(ref)

        read_assert_tag(f, 0x03)

    def write(self, f):
        write_u8(f, 0x02)
        write_u8(f, 0x01)

        write_s32le(f, len(self))
        for obj in self:
            write_object_ref(self.root, f, obj)

        write_u8(f, 0x03)

@utils.register_class
class TimeCrumbList(AVBRefList):
    class_id = b'TMCS'
    __slots__ = ()

    def read(self, f):
        read_assert_tag(f, 0x02)
        read_assert_tag(f, 0x01)

        count = read_s16le(f)
        for i in range(count):
            ref = read_object_ref(self.root, f)
            self.append(ref)

        read_assert_tag(f, 0x03)

    def write(self, f):
        write_u8(f, 0x02)
        write_u8(f, 0x01)

        write_s16le(f, len(self))
        for obj in self:
            write_object_ref(self.root, f, obj)

        write_u8(f, 0x03)
