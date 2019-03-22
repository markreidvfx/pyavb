from __future__ import (
    unicode_literals,
    absolute_import,
    print_function,
    division,
    )

from . import utils

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

class AVBPropertyData(dict):
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
    __slots__ = ('root', '__weakref__')
    def __init__(self, root):
        super(AVBRefList, self).__init__()
        self.root = root

    def deref(self, value):
        if isinstance(value, utils.AVBObjectRef):
            return value.value
        return value

    def __getattr__(self, index):
        return self.deref(super(AVBRefList, self).__getitem__(index))

    def __iter__(self):
        for value in super(AVBRefList, self).__iter__():
            yield self.deref(value)


class AVBObject(object):
    propertydefs = []
    __slots__ = ('root', 'property_data', '__weakref__')

    def __init__(self, root):
        self.root = root
        self.property_data = AVBPropertyData()

    def __setattr__(self, name, value):
        for item in self.propertydefs:
            if name == item.name:
                self.property_data[name] = value
                return

        super(AVBObject, self).__setattr__(name, value)

    def get_property_def(self, name):
        for item in self.propertydefs:
            if item.name == name:
                return item

    def __getattr__(self, name):
        if name in self.property_data:
            v =  self.property_data[name]
            if isinstance(v, utils.AVBObjectRef):
                return v.value
            # p_def = self.get_property_def(name)
            # if p_def.type == 'reference':
            #     return v

            return v
        raise AttributeError("'%s' has no attribute '%s'" % (self.__class__.__name__, name))
        # return super(AVBObject, self).__getattr__(name)

    def read(self, f):
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
