from __future__ import (
    unicode_literals,
    absolute_import,
    print_function,
    division,
    )
import os
import io
import binascii
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
        self.debug_copy_refs = True
        self.reading = True

def read_write_chunk(path):

    with io.open(path, 'rb') as f:
        m = MockFile(f)
        chunk = avb.file.read_chunk(m, f)
        obj_class = avb.utils.AVBClaseID_dict.get(chunk.class_id, None)
        assert obj_class
        try:
            object_instance = obj_class.__new__(obj_class, root=m)
            chunk_data = chunk.read()
            object_instance.read(io.BytesIO(chunk_data))
        except:
            print('read error:')
            print(path)
            print(chunk.class_id)
            print(chunk.hex())
            raise
        write_data = b''
        try:
            r = io.BytesIO()
            object_instance.write(r)
            write_data = r.getvalue()
            assert write_data == chunk_data
        except:
            print('write error:')
            print(path)
            print(chunk.class_id)
            print(binascii.hexlify(chunk_data))
            print()
            print(binascii.hexlify(write_data))
            raise

class TestChuckDB(unittest.TestCase):


    def test_cdci_chunks(self):
        for chunk_path in iter_chunks("CDCI"):
            read_write_chunk(chunk_path)

    def test_cmpo_chunks(self):
        for chunk_path in iter_chunks("CMPO"):
            read_write_chunk(chunk_path)

    def test_rgba_chunks(self):
        for chunk_path in iter_chunks("RGBA"):
            read_write_chunk(chunk_path)

    def test_rset_chunks(self):
        for chunk_path in iter_chunks("RSET"):
            read_write_chunk(chunk_path)

    def test_mdtp_chunks(self):
        for chunk_path in iter_chunks("MDTP"):
            read_write_chunk(chunk_path)

    def test_fxps_chunks(self):
        for chunk_path in iter_chunks("FXPS"):
            read_write_chunk(chunk_path)

    def test_file_chunks(self):
        for chunk_path in iter_chunks("FILE"):
            read_write_chunk(chunk_path)

    def test_rept_chunks(self):
        for chunk_path in iter_chunks("REPT"):
            read_write_chunk(chunk_path)

    def test_pvol_chunks(self):
        for chunk_path in iter_chunks("PVOL"):
            read_write_chunk(chunk_path)

    def test_slct_chunks(self):
        for chunk_path in iter_chunks("SLCT"):
            read_write_chunk(chunk_path)

    def test_mcmr_chunks(self):
        for chunk_path in iter_chunks("MCMR"):
            read_write_chunk(chunk_path)

    def test_mcbr_chunks(self):
        for chunk_path in iter_chunks('MCBR'):
            read_write_chunk(chunk_path)

    def test_msml_chunks(self):
        for chunk_path in iter_chunks('MSML'):
            read_write_chunk(chunk_path)

    def test_muld_chunks(self):
        for chunk_path in iter_chunks("MULD"):
            read_write_chunk(chunk_path)

    def test_didp_chunks(self):
        for chunk_path in iter_chunks("DIDP"):
            read_write_chunk(chunk_path)

    def test_ctrl_chunks(self):
        for chunk_path in iter_chunks("CTRL"):
            read_write_chunk(chunk_path)

    def test_tmbc_chunks(self):
        for chunk_path in iter_chunks("TMBC"):
            read_write_chunk(chunk_path)

    def test_prit_chunks(self):
        for chunk_path in iter_chunks("PRIT"):
            read_write_chunk(chunk_path)

    def test_prcl_chunks(self):
        for chunk_path in iter_chunks("PRCL"):
            read_write_chunk(chunk_path)

    def test_eqmb_chunks(self):
        for chunk_path in iter_chunks("EQMB"):
            read_write_chunk(chunk_path)

    def test_aspi_chunks(self):
        for chunk_path in iter_chunks("ASPI"):
            read_write_chunk(chunk_path)

    def test_tkds_chunks(self):
        for chunk_path in iter_chunks("TKDS"):
            read_write_chunk(chunk_path)

    def test_tnfx_chunks(self):
        for chunk_path in iter_chunks("TNFX"):
            read_write_chunk(chunk_path)

    def test_tkpa_chunks(self):
        for chunk_path in iter_chunks("TKPS"):
            read_write_chunk(chunk_path)

    def test_tkda_chunks(self):
        for chunk_path in iter_chunks("TKDA"):
            read_write_chunk(chunk_path)

    def test_tkpa_chunks(self):
        for chunk_path in iter_chunks("TKPA"):
            read_write_chunk(chunk_path)

    def test_winf_chunks(self):
        for chunk_path in iter_chunks("WINF"):
            read_write_chunk(chunk_path)

    def test_bvst_chunks(self):
        for chunk_path in iter_chunks("BVst"):
            read_write_chunk(chunk_path)

    def test_wave_chunks(self):
        for chunk_path in iter_chunks("WAVE"):
            read_write_chunk(chunk_path)

    def test_mpgi_chunks(self):
        for chunk_path in iter_chunks("MPGI"):
            read_write_chunk(chunk_path)

    def test_shlp_chunks(self):
        for chunk_path in iter_chunks("SHLP"):
            read_write_chunk(chunk_path)

if __name__ == "__main__":
    unittest.main()
