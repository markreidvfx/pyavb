from __future__ import (
    unicode_literals,
    absolute_import,
    print_function,
    division,
    )

from . import utils
from collections import OrderedDict

sentinel = object()

class AVBPropertyDef(object):
    __slots__ = ('name', 'long_name', 'type')
    def __init__(self, name, long_name, data_type, tag=None):
        self.name = name
        self.long_name = name
        self.type = data_type
    def __repr__(self):
        s = ""
        s += "%s.%s"  % (self.__class__.__module__,
                                self.__class__.__name__)

        s += " " + str(self.name)
        s += " " + str(self.type)

        return '<%s at 0x%x>' % (s, id(self))

class AVBPropertyData(OrderedDict):
    __slots__ = ()
    def deref(self, value):
        if isinstance(value, utils.AVBObjectRef):
            return value.value
        return value

    def __getitem__(self, key):
        return self.deref(super(AVBPropertyData, self).__getitem__(key))

    def items(self):
        for key, value in super(AVBPropertyData, self).items():
            yield key, self.deref(value)

    def get(self, *args, **kwargs):
        return self.deref(super(AVBPropertyData, self).get(*args, **kwargs))

class AVBRefList(list):
    __slots__ = ('root', 'instance_id', '__weakref__')

    def __new__(cls, *args, **kwargs):
        self = super(AVBRefList, cls).__new__(cls)
        self.root = kwargs.get("root", None)
        return self
    # def __init__(self, root):
    #     super(AVBRefList, self).__init__()
    #     self.root = root

    def mark_modified(self):
        if not self.root.reading:
            self.root.add_modified(self)

    def extend(self, x):
        super(AVBRefList, self).extend(x)
        self.mark_modified()

    def append(self, x):
        super(AVBRefList, self).append(x)
        self.mark_modified()

    def insert(self, i, x):
        super(AVBRefList, self).insert(i, x)
        self.mark_modified()

    def remove(self, x):
        super(AVBRefList, self).remove(x)
        self.mark_modified()

    def pop(self, i=-1):
        result = elf.deref(super(AVBRefList, self).pop(i))
        self.mark_modified()
        return result

    def clear(self):
        super(AVBRefList, self)
        self.mark_modified()

    def sort(key=None, reverse=False):
        super(AVBRefList, self)
        self.mark_modified()

    def reverse(self):
        super(AVBRefList, self)
        self.mark_modified()

    def deref(self, value):
        if isinstance(value, utils.AVBObjectRef):
            return value.value
        return value

    def __getitem__(self, index):
        return self.deref(super(AVBRefList, self).__getitem__(index))

    def __setitem__(self, index, value):
        super(AVBRefList, self).__setitem__(index, value)
        self.mark_modified()

    def __delitem__(self, index):
        super(AVBRefList, self).__delitem__(index)
        self.mark_modified()

    def __iter__(self):
        for value in super(AVBRefList, self).__iter__():
            yield self.deref(value)

def walk_references(obj):

    if isinstance(obj, list):
        property_values = obj
    elif isinstance(obj, dict):
        property_values = obj.values()
    elif hasattr(obj, 'property_data'):
        property_values = obj.property_data.values()
    else:
        property_values = []

    for v in property_values:
        if isinstance(v, utils.AVBObjectRef):
            v = v.value
        if v is None:
            continue

        if isinstance(v, list):
            for item in v:
                for sub_v in walk_references(item):
                    yield sub_v

        if hasattr(v, 'class_id'):
            for sub_v in walk_references(v):
                yield sub_v

    if hasattr(obj, 'class_id'):
        yield obj


class AVBObject(object):
    propertydefs = []
    __slots__ = ('root', 'property_data', 'instance_id', '__weakref__')

    def __new__(cls, *args, **kwargs):
        self = super(AVBObject, cls).__new__(cls)
        self.root = kwargs.get("root", None)
        self.property_data = AVBPropertyData()
        return self

    # def __init__(self, root):
    #     self.root = root
    #     self.property_data = AVBPropertyData()

    def mark_modified(self):
        if not self.root.reading:
            self.root.add_modified(self)

    def get_property_def(self, name):
        for item in self.propertydefs:
            if item.name == name:
                return item

    def __setattr__(self, name, value):
        if name != 'root':
            for item in self.propertydefs:
                if name == item.name:
                    self.property_data[name] = value
                    self.mark_modified()
                    return

        super(AVBObject, self).__setattr__(name, value)

    def __getattr__(self, name):
        v = self.property_data.get(name, sentinel)
        if v is not sentinel:
            if isinstance(v, utils.AVBObjectRef):
                return v.value
            return v

        raise AttributeError("'%s' has no attribute '%s'" % (self.__class__.__name__, name))

    def read(self, f):
        pass

    def write(self, f):
        pass

    def __repr__(self):
        s = "%s.%s"  % (self.__class__.__module__,
                                self.__class__.__name__)

        if hasattr(self, 'class_id') and self.class_id:
            s = str(self.class_id) + " " + s

        if hasattr(self, 'name') and self.name:
            s += " " + self.name

        if hasattr(self, 'mob_type') and self.mob_type:
            s += " " + self.mob_type

        if hasattr(self, 'effect_id') and self.effect_id:

            s += " " + self.effect_id

        if hasattr(self, 'media_kind') and self.media_kind:
            s += " "  + str(self.media_kind)

        if hasattr(self, 'length'):
            s += " len: " + str(self.length)

        if hasattr(self, 'track_id'):
            s += ' track_id: ' + str(self.track_id)

        if hasattr(self, 'start_time'):
            s += ' start_time: ' + str(self.start_time)

        if hasattr(self, 'mob_id'):
            s += " " + str(self.mob_id)

        if hasattr(self, 'uuid'):
            s += " " + str(self.uuid)

        if hasattr(self, 'value'):
            s += " " + str(self.value)

        return '<%s at 0x%x>' % (s, id(self))
