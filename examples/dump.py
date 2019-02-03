from __future__ import (
    unicode_literals,
    absolute_import,
    print_function,
    division,
    )
import avb
import sys


# def dump(item, space=''):
#
#
#     if isinstance(item, avb.utils.AVBObjectRef):
#         dump(item.value, space)
#         return
#
#     if not isinstance(item, avb.core.AVBObject):
#         if item is None:
#             return
#         s = str(item)
#         if s:
#             print space, s
#         return
#
#     for name, value in item.properties():
#         print space, name, type(value), ':',
#         if isinstance(value, list):
#             print 'len:', len(value)
#             for obj in value:
#                 dump(obj, space + " ")
#         else:
#             print "";
#             dump(value, space + "  ")
#

if bytes is not str:
    unicode = str

def pretty_value(value):
    if isinstance(value, bytearray):
        return "bytearray(%d)" % len(value)
        # return ''.join(format(x, '02x') for x in value)
    return value

def dump_obj(obj):

    for pdef in obj.propertydefs:
        key = pdef.name
        if key in obj.property_data:

            value = obj.property_data[key]
            if isinstance(value, dict):
                print("%s:" % key)
                for sub_key, sub_value in value.items():
                    print("  ", "%s:" % sub_key, unicode(sub_value))

            elif isinstance(value, list):
                print("%s:" % key)
                for sub_value in value:
                    if isinstance(sub_value, avb.trackgroups.Track):
                        for ref in sub_value.refs:
                            print("     ", type(ref.value), ref.value )
                    else:
                        print("  ", sub_value)

            else:
                print("%s:" % key , obj.property_data[key])

def dump(obj, space=""):

    if isinstance(obj, dict):
        for key, value in obj.items():
            if isinstance(value, avb.core.AVBObject):
                print("%s%s:" % (space, key))
                dump(value, space + " ")
            elif isinstance(value, dict):
                print("%s%s:" % (space, key))
                dump(value, space + " ")

            elif isinstance(value, list):
                print("%s%s:" % (space, key))
                for item in value:
                    dump(item, space + " ")
            else:
                if value is not None:
                    print("%s%s:" % (space, key), pretty_value(value))
        return

    if not isinstance(obj, avb.core.AVBObject):
        print(space, obj)
        return
    print(space, unicode(obj))
    space += "  "
    for pdef in obj.propertydefs:
        key = pdef.name
        if key not in obj.property_data:
            continue
        value = obj.property_data[key]
        if isinstance(value, avb.core.AVBObject):
            print("%s%s:" % (space, key))
            dump(value, space + " ")
        elif isinstance(value, list):
            print("%s%s:" % (space, key))
            for item in value:
                dump(item, space + " ")
        elif isinstance(value, dict):
            print("%s%s:" % (space, key))
            dump(value, space + " ")
        else:
            if value is not None:
                print("%s%s:" % (space, key), pretty_value(value))


def main(path):
    with avb.open(path) as f:
        dump(f.content)


if __name__ == "__main__":

    main(sys.argv[1])
