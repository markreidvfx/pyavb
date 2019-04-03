from __future__ import (
    unicode_literals,
    absolute_import,
    print_function,
    division,
    )
import avb
import sys

if bytes is not str:
    unicode = str

def pretty_value(value):
    if isinstance(value, bytearray):
        return "bytearray(%d)" % len(value)
        # return ''.join(format(x, '02x') for x in value)
    return value

def dump(obj, space=""):

    propertie_keys = []
    property_data = None
    if isinstance(obj, avb.core.AVBObject):
        print(space, unicode(obj))
        space += "  "
        property_data = obj.property_data
        for pdef in obj.propertydefs:
            key = pdef.name
            if key not in obj.property_data:
                continue
            propertie_keys.append(key)

    elif isinstance(obj, dict):
        propertie_keys = list(obj.keys())
        propertie_keys.sort()
        property_data = obj
    else:
        print(space, obj)
        return

    for key in propertie_keys:
        value = property_data[key]
        if isinstance(value, (avb.core.AVBObject, dict)):
            print("%s%s:" % (space, key))
            dump(value, space + " ")
        elif isinstance(value, list):
            print("%s%s:" % (space, key))
            for item in value:
                dump(item, space + " ")
        else:
            if value is not None:
                print("%s%s:" % (space, key), pretty_value(value))


def main(path):
    with avb.open(path) as f:
        dump(f.content)

if __name__ == "__main__":

    main(sys.argv[1])
