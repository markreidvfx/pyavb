from __future__ import (
    unicode_literals,
    absolute_import,
    print_function,
    division,
    )
import os
import io
import unittest
import avb

import avb.utils
import glob

def iter_chunks(chunk_type):
    chunk_dir = os.path.join(os.path.dirname(__file__), 'chunks', chunk_type, '*.chunk')

    for item in glob.glob(chunk_dir):
        yield item

class MockFile(object):
    def __init__(self, f):
        self.f = f
        self.check_refs = False

def decode_chunk(path):

    with io.open(path, 'rb') as f:
        m = MockFile(f)
        chunk = avb.file.read_chunk(m, f)
        obj_class = avb.utils.AVBClaseID_dict.get(chunk.class_id, None)
        assert obj_class
        try:
            object_instance = obj_class(m)
            object_instance.read(io.BytesIO(chunk.read()))
        except:
            print(path)
            print(chunk.class_id)
            print(chunk.hex())
            raise

class TestChuckDB(unittest.TestCase):


    def test_cdci_chunks(self):
        for chunk_path in iter_chunks("CDCI"):
            decode_chunk(chunk_path)

    def test_cmpo_chunks(self):
        for chunk_path in iter_chunks("CMPO"):
            decode_chunk(chunk_path)

    def test_rgba_chunks(self):
        for chunk_path in iter_chunks("RGBA"):
            decode_chunk(chunk_path)

    def test_rset_chunks(self):
        for chunk_path in iter_chunks("RSET"):
            decode_chunk(chunk_path)

    def test_mdtp_chunks(self):
        for chunk_path in iter_chunks("MDTP"):
            decode_chunk(chunk_path)

    def test_rept_chunks(self):
        for chunk_path in iter_chunks("REPT"):
            decode_chunk(chunk_path)

    def test_pvol_chunks(self):
        for chunk_path in iter_chunks("PVOL"):
            decode_chunk(chunk_path)

    def test_slct_chunks(self):
        for chunk_path in iter_chunks("SLCT"):
            decode_chunk(chunk_path)

    def test_mcmr_chunks(self):
        for chunk_path in iter_chunks("MCMR"):
            decode_chunk(chunk_path)

    def test_mcbr_chunks(self):
        for chunk_path in iter_chunks('MCBR'):
            decode_chunk(chunk_path)

    def test_msml_chunks(self):
        for chunk_path in iter_chunks('MSML'):
            decode_chunk(chunk_path)

    def test_muld_chunks(self):
        for chunk_path in iter_chunks("MULD"):
            decode_chunk(chunk_path)


    def test_ctrl_chunks(self):
        for chunk_path in iter_chunks("CTRL"):
            decode_chunk(chunk_path)

    def test_tmbc_chunks(self):
        for chunk_path in iter_chunks("TMBC"):
            decode_chunk(chunk_path)

    def test_prit_chunks(self):
        for chunk_path in iter_chunks("PRIT"):
            decode_chunk(chunk_path)

    def test_prcl_chunks(self):
        for chunk_path in iter_chunks("PRCL"):
            decode_chunk(chunk_path)

    def test_eqmb_chunks(self):
        for chunk_path in iter_chunks("EQMB"):
            decode_chunk(chunk_path)

    def test_aspi_chunks(self):
        for chunk_path in iter_chunks("ASPI"):
            decode_chunk(chunk_path)
if __name__ == "__main__":
    unittest.main()
