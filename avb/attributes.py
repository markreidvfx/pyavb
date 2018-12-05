from __future__ import (
    unicode_literals,
    absolute_import,
    print_function,
    division,
    )

from . import utils
from . import core
from .core import AVBPropertyDef

from . utils import (
    read_byte,
    read_s16le,
    read_u32le,
    read_s32le,
    read_string,
    read_object_ref,
    peek_data,
)

INT_ATTR  = 1
STR_ATTR  = 2
OBJ_ATTR  = 3
BOB_ATTR  = 4

@utils.register_class
class Attributes(dict):
    class_id = b'ATTR'

    def __init__(self, root):
        super(Attributes, self).__init__()
        self.root = root

    def read(self, f):
        assert read_byte(f) == 0x02
        assert read_byte(f) == 0x01

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
                result[attr_name] = f.read(size)
            else:
                raise Exception("Unkown attr name: %s type: %d" % ( attr_name, attr_type))

        # print("read", result)
        self.update(result)

class RefList(list):

    def __init__(self, root):
        super(RefList, self).__init__()
        self.root = root

@utils.register_class
class ParameterList(RefList):
    class_id = b'PRLS'

    def read(self, f):
        assert read_byte(f) == 0x02
        assert read_byte(f) == 0x01

        count = read_s32le(f)
        for i in range(count):
            ref = read_object_ref(self.root, f)
            self.append(ref)

        assert read_byte(f) == 0x03

@utils.register_class
class TimeCrumbList(RefList):
    class_id = b'TMCS'

    def read(self, f):
        assert read_byte(f) == 0x02
        assert read_byte(f) == 0x01

        count = read_s16le(f)
        for i in range(count):
            ref = read_object_ref(self.root, f)
            self.append(ref)

        assert read_byte(f) == 0x03
