import tempfile
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from swcell_check_flash_image import check_images


def record(address, kind, payload=b""):
    body=bytes([len(payload),address>>8,address&255,kind])+payload
    return ":"+(body+bytes([(-sum(body))&255])).hex()+"\n"


class FlashImageTests(unittest.TestCase):
    def verify(self, mcs, binary):
        with tempfile.TemporaryDirectory() as tmp:
            m,b=Path(tmp)/"image.mcs",Path(tmp)/"image.bin"
            m.write_text(mcs);b.write_bytes(binary)
            return check_images(m,b)

    def test_valid_and_extended_address(self):
        payload=b"x"*65536+b"end"
        lines=record(0,4,b"\0\0")
        lines+="".join(record(i,0,payload[i:i+32]) for i in range(0,65536,32))
        lines+=record(0,4,b"\0\1")+record(0,0,b"end")+record(0,1)
        result=self.verify(lines,payload)
        self.assertEqual(result["image_bytes"],65539)
        self.assertEqual(result["start_address"],0)

    def test_checksum_corruption(self):
        with self.assertRaises(ValueError):
            self.verify(":010000000100\n"+record(0,1),b"\1")

    def test_truncated_or_extra_records(self):
        for text in (record(0,0,b"test"),record(0,0,b"test")+record(0,1)+record(0,4,b"\0\0")):
            with self.subTest(text=text),self.assertRaises(ValueError):
                self.verify(text,b"test")

    def test_binary_mismatch(self):
        with self.assertRaises(ValueError):
            self.verify(record(0,0,b"wrong")+record(0,1),b"right")

    def test_overlap_gap_and_capacity(self):
        for text in (record(1,0,b"bad")+record(0,1),
                     record(0,0,b"bad")+record(0,0,b"bad")+record(0,1),
                     record(0,4,b"\x02\x00")+record(0,0,b"bad")+record(0,1)):
            with self.subTest(text=text),self.assertRaises(ValueError):
                self.verify(text,b"bad")


if __name__=="__main__":
    unittest.main()
