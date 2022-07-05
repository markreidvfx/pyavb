from __future__ import (
    unicode_literals,
    absolute_import,
    print_function,
    division,
    )
import os
import avb
import unittest
from uuid import UUID

TEST_FILES_DIR = os.path.join(os.path.dirname(__file__), 'test_files')

PARAM_SPEED_MAP_U_ID = UUID("8d56827c-847e-11d5-935a-50f857c10000")
PARAM_SPEED_OFFSET_MAP_U_ID = UUID("8d56827d-847e-11d5-935a-50f857c10000")

def find_retime(f):
    speed_map = None
    offset_map = None
    motion_effect = None

    for comp in f.iter_class_ids([b'SPED']):
        motion_effect = comp
        for param in comp.param_list:
            if param.uuid == PARAM_SPEED_MAP_U_ID:
                speed_map = param
            elif param.uuid == PARAM_SPEED_OFFSET_MAP_U_ID:
                offset_map = param

        return comp, speed_map, offset_map

def compare_speedmap_to_offset_map(path):

    with avb.open(path) as f:
        motion_effect, speed_map, offset_map = find_retime(f)
        start = offset_map.control_track.control_points[0].time

        length = motion_effect.length

        error_list = []

        for t, v in speed_map.control_track.integrate(int(start), length):
            target_value = offset_map.control_track.value_at(t)
            error_list.append(abs(target_value - v))

        # print("average error:", sum(error_list) / len(error_list))

        return sum(error_list) / len(error_list)

def error_ok(value, path):
    # print(os.path.basename(path), 'error =', value)
    if value > 1.0e-07:
        return False
    return True

class TestRetime(unittest.TestCase):

    def test_speedmap_step(self):
        test_file = os.path.join(TEST_FILES_DIR,'retimes/step01.avb')
        error = compare_speedmap_to_offset_map(test_file)
        self.assertTrue(error_ok(error, test_file))
        test_file = os.path.join(TEST_FILES_DIR, 'retimes/step02.avb')
        error = compare_speedmap_to_offset_map(test_file)
        self.assertTrue(error_ok(error, test_file))
        test_file = os.path.join(TEST_FILES_DIR, 'retimes/step03.avb')
        error = compare_speedmap_to_offset_map(test_file)
        self.assertTrue(error_ok(error, test_file))

    def test_speedmap_linear(self):
        test_file = os.path.join(TEST_FILES_DIR, 'retimes/linear01.avb')
        error = compare_speedmap_to_offset_map(test_file)
        self.assertTrue(error_ok(error, test_file))
        test_file = os.path.join(TEST_FILES_DIR, 'retimes/linear02.avb')
        error = compare_speedmap_to_offset_map(test_file)
        self.assertTrue(error_ok(error, test_file))
        test_file = os.path.join(TEST_FILES_DIR, 'retimes/linear03.avb')
        error = compare_speedmap_to_offset_map(test_file)
        self.assertTrue(error_ok(error, test_file))

    def test_speedmap_spline(self):
        test_file = os.path.join(TEST_FILES_DIR, 'retimes/spline01.avb')
        error = compare_speedmap_to_offset_map(test_file)
        self.assertTrue(error_ok(error, test_file))
        test_file = os.path.join(TEST_FILES_DIR, 'retimes/spline02.avb')
        error = compare_speedmap_to_offset_map(test_file)
        self.assertTrue(error_ok(error, test_file))
        test_file = os.path.join(TEST_FILES_DIR, 'retimes/spline03.avb')
        error = compare_speedmap_to_offset_map(test_file)
        self.assertTrue(error_ok(error, test_file))

    def test_speedmap_bezier(self):
        test_file = os.path.join(TEST_FILES_DIR, 'retimes/bezier01.avb')
        error = compare_speedmap_to_offset_map(test_file)
        self.assertTrue(error_ok(error, test_file))
        test_file = os.path.join(TEST_FILES_DIR, 'retimes/bezier02.avb')
        error = compare_speedmap_to_offset_map(test_file)
        self.assertTrue(error_ok(error, test_file))
        test_file = os.path.join(TEST_FILES_DIR, 'retimes/bezier03.avb')
        error = compare_speedmap_to_offset_map(test_file)
        self.assertTrue(error_ok(error, test_file))

    def skip_test_retime_manually(self):

        test_file = os.path.join(TEST_FILES_DIR, 'retimes/bezier01.avb')
        # test_file = os.path.join(TEST_FILES_DIR, 'retimes/spline01.avb')
        # test_file = os.path.join(TEST_FILES_DIR, 'retimes/step01.avb')
        # compare_speedmap_to_offset_map(test_file)

        # manual testing here

        import matplotlib.pyplot as plt
        import numpy as np

        with avb.open(test_file) as f:
            motion_effect, speed_map, offset_map = find_retime(f)

            target =[[], []]

            print(speed_map)
            print (offset_map)

            p0 = offset_map.control_track.control_points[0]
            sp0 = speed_map.control_track.control_points[0]
            for item in offset_map.control_track.control_points:
                target[0].append(item.time)
                target[1].append(item.value)
                print(item.time, item.value)

            start = int(p0.time)
            print(p0.time)
            # op_group[1].dump()

            # print(end, p_last.time)
            pos = 0
            error_list = []

            offset_map_gen = speed_map.control_track.integrate(start, motion_effect.length)
            calcuated = [[], []]
            for t,v in offset_map_gen:
                calcuated[0].append(t)
                calcuated[1].append(v)
                tar = offset_map.control_track.value_at(t)
                error = abs(tar - v)
                print(t, error, tar, pos)
                error_list.append(error)

            print("average error:", sum(error_list) / len(error_list))


            plt.plot(target[0], target[1])
            plt.plot(calcuated[0], calcuated[1])

            plt.show()


if __name__ == "__main__":
    import logging
    unittest.main()
