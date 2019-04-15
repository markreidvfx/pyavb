from __future__ import (
    unicode_literals,
    absolute_import,
    print_function,
    division,
    )
import os
import unittest
import avb

import avb.utils
from avb.ioctx import AVBIOContext

test_file_01 = os.path.join(os.path.dirname(__file__), 'test_files', 'test_file_01.avb')

result_dir = os.path.join(os.path.dirname(__file__), 'results')

if not os.path.exists(result_dir):
    os.makedirs(result_dir)

def compare(a, b):
    a_property_data = None
    a_propertie_keys = []
    if isinstance(a, avb.utils.AVBObjectRef):
        a = a.value
        b = b.value

    if isinstance(a, avb.core.AVBObject):
        a_property_data = a.property_data
        a_propertie_keys = list(a_property_data.keys())

        b_property_data = b.property_data
        b_propertie_keys = list(b_property_data.keys())


    elif isinstance(a, dict):
        a_property_data = a
        a_propertie_keys = list(a.keys())

        b_property_data = b
        b_propertie_keys = list(b.keys())
    else:
        # print(a, b)
        assert a == b

    for key in a_propertie_keys:
        assert key in b_property_data

        a_value = a_property_data[key]
        b_value = b_property_data[key]

        assert type(a_value) == type(b_value)

        if isinstance(a_value, (avb.core.AVBObject, dict)):
            compare(a_value, b_value)

        elif isinstance(a_value, list):
            assert len(a_value) == len(b_value)
            for i in range(len(a_value)):
                compare(a_value[i], b_value[i])

        else:
            assert a_value == b_value


class TestWrite(unittest.TestCase):

    def test_rewrite_all(self):

        result_file = os.path.join(result_dir, 'rewrite_all.avb')
        with avb.open(test_file_01) as f:
            f.write(result_file)

        with avb.open(test_file_01) as a:
            with avb.open(result_file) as b:
                compare(a.content, b.content)

    def test_rewrite_all(self):

        result_file = os.path.join(result_dir, 'rewrite_be.avb')
        with avb.open(test_file_01) as f:
            f.write(result_file, byte_order='big')

        with avb.open(test_file_01) as a:
            with avb.open(result_file) as b:
                compare(a.content, b.content)

    def test_rewrite(self):
        result_file = os.path.join(result_dir, 'rewrite.avb')

        with avb.open(test_file_01) as f:
            f.debug_copy_refs = True
            f.octx = AVBIOContext()

            with open(result_file, 'wb') as f2:

                count_pos = f.write_header(f2)
                obj_count = len(f.object_positions)

                pos = f2.tell()
                f2.seek(count_pos)
                AVBIOContext.write_u32le(f2, obj_count-1)
                AVBIOContext.write_u32le(f2, obj_count-1)
                f2.seek(pos)

                for i in range(1,  obj_count):
                    obj = f.read_object(i)
                    f.write_object(f2, obj)

        with avb.open(test_file_01) as a:
            with avb.open(result_file) as b:
                s = f.object_positions[1]
                a.f.seek(s)
                b.f.seek(s)
                assert a.f.read() == b.f.read()

    def test_no_modify(self):
        result_file = os.path.join(result_dir, 'modifed.avb')
        with avb.open(test_file_01) as f:
            for mob in f.content.mobs:
                for track in mob.tracks:
                    c = track.component
                    if isinstance(c, avb.components.Sequence):
                        for item in c.components:
                            pass

            # nothin should be modified
            assert not f.modified_objects

    def test_modify(self):
        result_file = os.path.join(result_dir, 'modifed.avb')
        with avb.open(test_file_01) as f:
            for mob in f.content.mobs:
                mob.name = u"Cow"
                mob.attributes['Test'] = 5

            assert f.modified_objects
            f.write(result_file)

        with avb.open(result_file) as f:
            for mob in f.content.mobs:
                assert mob.name == u"Cow"
                assert mob.attributes['Test'] == 5


if __name__ == "__main__":
    unittest.main()
