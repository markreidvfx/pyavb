from __future__ import (
    unicode_literals,
    absolute_import,
    print_function,
    division,
    )

from . import core
from . import utils
from .core import AVBProperty

from . utils import (
    read_byte,
    read_s8,
    read_bool,
    read_s16le,
    read_u16le,
    read_u32le,
    read_s32le,
    read_string,
    read_doublele,
    read_exp10_encoded_float,
    read_object_ref,
    read_datetime,
    iter_ext,
    read_assert_tag,
    peek_data
)

@utils.register_class
class FileLocator(core.AVBObject):
    class_id = b'FILE'
    properties = [
        AVBProperty('path_name', 'OMFI:FL:PathName', 'string'),
        AVBProperty('paths',     'OMFI:FL:Paths',     'list'),
    ]

    def read(self, f):
        super(FileLocator, self).read(f)

        tag = read_byte(f)
        version = read_byte(f)

        assert tag == 0x02
        assert version == 2
        self.paths = []
        path = read_string(f)
        if path:
            self.path_name= path

        for tag in iter_ext(f):
            if tag == 0x01:
                read_assert_tag(f, 76)
                path = read_string(f)
                if path:
                    self.paths.append(path)

            elif tag == 0x02:
                read_assert_tag(f, 76)
                # utf-8?
                path = read_string(f)
                if path:
                    self.paths.append(path)
            else:
                raise ValueError("%s: unknown ext tag 0x%02X %d" % (str(self.class_id), tag,tag))

        tag = read_byte(f)
        assert tag == 0x03

@utils.register_class
class GraphicEffect(core.AVBObject):
    class_id = b'GRFX'
    properties = [
        AVBProperty('pict_data', 'OMFI:MC:GRFX:PictData', 'bytes'),
    ]
    def read(self, f):

        read_assert_tag(f, 0x02)
        read_assert_tag(f, 0x01)

        pict_size = read_s32le(f)
        assert pict_size >= 0

        self.pict_data = bytearray(f.read(pict_size))
        assert len(self.pict_data) == pict_size

        read_assert_tag(f, 0x03)
