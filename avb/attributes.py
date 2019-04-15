from __future__ import (
    unicode_literals,
    absolute_import,
    print_function,
    division,
    )

from . import utils
from . import core
from .core import AVBPropertyDef, AVBPropertyData, AVBRefList
from . utils import peek_data

INT_ATTR  = 1
STR_ATTR  = 2
OBJ_ATTR  = 3
BOB_ATTR  = 4

if bytes is not str:
    unicode = str

@utils.register_class
class Attributes(AVBPropertyData):
    class_id = b'ATTR'
    propertydefs = []
    __slots__ = ('root', 'instance_id', )

    def __new__(cls, *args, **kwargs):
        self = super(Attributes, cls).__new__(cls)
        self.root = kwargs.get('root', None)
        return self

    def mark_modified(self):
        if not self.root.reading:
            self.root.add_modified(self)

    def __setitem__(self, key, value):
        super(Attributes, self).__setitem__(key, value)
        self.mark_modified()

    def __delitem__(self, key):
        super(Attributes, self).__delitem__(key)
        self.mark_modified()

    def clear(self):
        super(Attributes, self).clear()
        self.mark_modified()

    def pop(self, *args, **kwargs):
        result = super(Attributes, self).pop(*args, **kwargs)
        self.mark_modified()
        return result

    def read(self, f):
        ctx = self.root.ictx
        ctx.read_assert_tag(f, 0x02)
        ctx.read_assert_tag(f, 0x01)

        count = ctx.read_u32(f)


        for i in range(count):
            attr_type = ctx.read_u32(f)
            attr_name = ctx.read_string(f)

            if attr_type == INT_ATTR:
                self[attr_name] = ctx.read_s32(f)
            elif attr_type == STR_ATTR:
                self[attr_name] = ctx.read_string(f)
            elif attr_type == OBJ_ATTR:
                self[attr_name] = ctx.read_object_ref(self.root, f)
            elif attr_type == BOB_ATTR:
                size = ctx.read_u32(f)
                self[attr_name] = bytearray(f.read(size))
            else:
                raise Exception("Unkown attr name: %s type: %d" % ( attr_name, attr_type))

        # print("read", result)

        ctx.read_assert_tag(f, 0x03)

    def write(self, f):
        ctx = self.root.octx
        ctx.write_u8(f, 0x02)
        ctx.write_u8(f, 0x01)

        ctx.write_u32(f, len(self))
        for key, value in self.items():
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

            ctx.write_u32(f, attr_type)
            ctx.write_string(f, key)

            if attr_type == INT_ATTR:
                ctx.write_s32(f, value)
            elif attr_type == STR_ATTR:
                ctx.write_string(f, value)
            elif attr_type == OBJ_ATTR:
                ctx.write_object_ref(self.root, f, value)
            elif attr_type == BOB_ATTR:
                ctx.write_u32(f, len(value))
                f.write(value)

        ctx.write_u8(f, 0x03)

@utils.register_class
class ParameterList(AVBRefList):
    class_id = b'PRLS'
    __slots__ = ()
    def read(self, f):
        ctx = self.root.ictx
        ctx.read_assert_tag(f, 0x02)
        ctx.read_assert_tag(f, 0x01)

        count = ctx.read_s32(f)
        for i in range(count):
            ref = ctx.read_object_ref(self.root, f)
            self.append(ref)

        ctx.read_assert_tag(f, 0x03)

    def write(self, f):
        ctx = self.root.octx
        ctx.write_u8(f, 0x02)
        ctx.write_u8(f, 0x01)

        ctx.write_s32(f, len(self))
        for obj in self:
            ctx.write_object_ref(self.root, f, obj)

        ctx.write_u8(f, 0x03)

@utils.register_class
class TimeCrumbList(AVBRefList):
    class_id = b'TMCS'
    __slots__ = ()

    def read(self, f):
        ctx = self.root.ictx
        ctx.read_assert_tag(f, 0x02)
        ctx.read_assert_tag(f, 0x01)

        count = ctx.read_s16(f)
        for i in range(count):
            ref = ctx.read_object_ref(self.root, f)
            self.append(ref)

        ctx.read_assert_tag(f, 0x03)

    def write(self, f):
        ctx = self.root.octx
        ctx.write_u8(f, 0x02)
        ctx.write_u8(f, 0x01)

        ctx.write_s16(f, len(self))
        for obj in self:
            ctx.write_object_ref(self.root, f, obj)

        ctx.write_u8(f, 0x03)
