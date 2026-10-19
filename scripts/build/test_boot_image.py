"""Safety tests use synthetic ordinary files only; no device/backup is opened."""
from pathlib import Path
import contextlib
import hashlib
import importlib.util
import io
import struct
import tempfile
import unittest
import os
import sys
sys.dont_write_bytecode = True

spec = importlib.util.spec_from_file_location('packager', Path(__file__).with_name('make_boot_image.py'))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class PackagerSafety(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=os.environ.get('YOUNG2_TEST_TMPDIR'))
        self.dir = Path(self.tmp.name)
        self.original = self.dir/'original.img'
        self.kernel = self.dir/'new.zImage'
        self.output = self.dir/'output'
        head = bytearray(2048)
        head[:8] = b'ANDROID!'
        struct.pack_into('<8I', head, 8, 1024, 0x8000, 1024, 0x1000000, 0, 0xf00000, 0x100, 2048)
        head[600:620] = b'preserve-header-data'
        self.ramdisk = b'R'*1024
        mod.EXPECT_RAMDISK = hashlib.sha256(self.ramdisk).hexdigest()
        self.origbytes = bytes(head)+b'K'*1024+b'\0'*1024+self.ramdisk+b'\0'*1024
        self.original.write_bytes(self.origbytes)
        self.kernel.write_bytes(b'N'*4096)

    def tearDown(self):
        self.tmp.cleanup()

    def run_packager(self):
        with contextlib.redirect_stdout(io.StringIO()):
            return mod.main(str(self.original),str(self.kernel),str(self.output))

    def test_header_ramdisk_and_boundary(self):
        self.assertEqual(self.run_packager(),0)
        data=(self.output/'candidate-p11-first-0x384000.bin').read_bytes()
        self.assertEqual(len(data),0x384000)
        self.assertEqual(data[:8]+data[12:2048],self.origbytes[:8]+self.origbytes[12:2048])
        self.assertEqual(data[6144:7168],self.ramdisk)
        self.assertEqual(self.original.read_bytes(),self.origbytes)

    def test_oversize_emits_nothing(self):
        self.kernel.write_bytes(b'N'*0x384000)
        with self.assertRaises(SystemExit): self.run_packager()
        self.assertFalse(self.output.exists())

    def test_existing_output_untouched(self):
        self.output.mkdir()
        marker=self.output/'keep'
        marker.write_bytes(b'unchanged')
        with self.assertRaises(SystemExit): self.run_packager()
        self.assertEqual(marker.read_bytes(),b'unchanged')

    def test_bad_ramdisk_rejected(self):
        mod.EXPECT_RAMDISK='0'*64
        with self.assertRaises(SystemExit): self.run_packager()
        self.assertFalse(self.output.exists())

    def test_wrong_geometry_rejected(self):
        data=bytearray(self.origbytes)
        struct.pack_into('<I',data,36,4096)
        self.original.write_bytes(data)
        with self.assertRaises(SystemExit): self.run_packager()
        self.assertFalse(self.output.exists())

    def test_truncation_rejected(self):
        self.original.write_bytes(self.origbytes[:4096])
        with self.assertRaises(SystemExit): self.run_packager()
        self.assertFalse(self.output.exists())

    def test_failed_check_propagates(self):
        real=mod.sha256
        calls=0
        def corrupt_late(data):
            nonlocal calls
            calls+=1
            return '0'*64 if calls==5 else real(data)
        mod.sha256=corrupt_late
        try:
            with self.assertRaises(SystemExit): self.run_packager()
        finally:
            mod.sha256=real

if __name__=='__main__':
    unittest.main(verbosity=2)
