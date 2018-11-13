from __future__ import (
    unicode_literals,
    absolute_import,
    print_function,
    division,
    )


class AVBObject(object):
    def __init__(self, root):
        self.root = root

    def read(self, f):
        pass

    def __repr__(self):
        s = "%s.%s"  % (self.__class__.__module__,
                                self.__class__.__name__)
        s = self.class_id + " " + s

        if hasattr(self, 'name') and self.name:
            s += " " + self.name

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
