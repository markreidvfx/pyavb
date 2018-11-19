from __future__ import (
    unicode_literals,
    absolute_import,
    print_function,
    division,
    )

from . import utils

from . utils import (
    read_byte,
    read_u32le,
    read_s32le,
    read_string,
    read_object_ref
)

INT_ATTR  = 1
STR_ATTR  = 2
OBJ_ATTR  = 3
BOB_ATTR  = 4

def read_attributes(root, f):
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
            result[attr_name] = read_object_ref(root, f)
        elif attr_type == BOB_ATTR:
            size = read_u32le(f)
            result[attr_name] = f.read(size)
        else:
            raise Exception("Unkown attr name: %s type: %d" % ( attr_name, attr_type))

    # print("read", result)
    return result

def read_paramlist(root, f):
    assert read_byte(f) == 0x02
    assert read_byte(f) == 0x01

    count = read_int32le(f)
    items = []
    for i in range(count):
        ref = read_object_ref(root, f)
        items.append(ref.resolve())

    assert read_byte(f) == 0x03

    return items
