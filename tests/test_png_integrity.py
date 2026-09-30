"""F03: PNG container/decode and complete remote/local identity checks."""

import io
import json
import struct
import sys
import tempfile
import time
import unittest
import zlib
from pathlib import Path
from unittest import mock

from PIL import Image

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
from scenario_a import codex_to_comfy as execution


def png(color=(40, 50, 60)):
    stream = io.BytesIO()
    Image.new("RGB", (2, 2), color).save(stream, format="PNG")
    return stream.getvalue()


class PNGIntegrityTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.comfy = self.root / "Comfy-UI"
        self.output = self.comfy / "work/output/proof/fresh.png"
        self.output.parent.mkdir(parents=True)
        self.record = {"status": {"status_str": "success"},
                       "outputs": {"13": {"images": [
                           {"filename": "fresh.png", "subfolder": "proof", "type": "output"}]}}}

    def verify(self, local, remote=None):
        self.output.write_bytes(local)
        with mock.patch.object(execution.urllib.request, "urlopen",
                               return_value=io.BytesIO(local if remote is None else remote)):
            return execution.verify_images(self.record, "13", self.comfy)

    def test_valid_png_passes_with_decoded_dimensions(self):
        result = self.verify(png())
        self.assertEqual(result, [{"type": "image", "path": str(self.output),
                                   "width": 2, "height": 2}])

    def test_header_with_garbage_payload_rejected(self):
        data = b"\x89PNG\r\n\x1a\n" + struct.pack(">I4sII", 13, b"IHDR", 768, 768) + b"garbage"
        with self.assertRaisesRegex(ValueError, "PNG"):
            self.verify(data)

    def test_truncated_png_and_missing_iend_rejected(self):
        valid = png()
        for data in (valid[:-12], valid[:-1], valid[:24]):
            with self.subTest(length=len(data)), self.assertRaisesRegex(ValueError, "PNG"):
                self.verify(data)

    def test_corrupt_idat_crc_rejected(self):
        data = bytearray(png())
        index = data.index(b"IDAT")
        data[index + 4] ^= 1
        with self.assertRaisesRegex(ValueError, "PNG"):
            self.verify(bytes(data))

    def test_undecodable_idat_with_valid_crc_rejected(self):
        data = bytearray(png())
        index = data.index(b"IDAT")
        length = struct.unpack(">I", data[index - 4:index])[0]
        data[index + 4:index + 4 + length] = b"\x00" * length
        crc = zlib.crc32(data[index:index + 4 + length])
        data[index + 4 + length:index + 8 + length] = struct.pack(">I", crc)
        with self.assertRaisesRegex(ValueError, "PNG"):
            self.verify(bytes(data))

    def test_same_header_different_valid_payload_rejected(self):
        local, remote = png(), png((80, 90, 100))
        self.assertEqual(local[:24], remote[:24])
        self.assertNotEqual(local, remote)
        with self.assertRaisesRegex(ValueError, "remote/local payload differs"):
            self.verify(local, remote)

    def test_corrupt_iend_crc_rejected(self):
        data = bytearray(png())
        data[-1] ^= 1
        with self.assertRaisesRegex(ValueError, "IEND"):
            self.verify(bytes(data))

    def test_premature_iend_with_extra_payload_rejected(self):
        data = png() + b"trailing garbage" + png()[-12:]
        with self.assertRaisesRegex(ValueError, "PNG"):
            self.verify(data)

    def test_corrupt_png_cannot_be_recorded_as_success(self):
        data = png()[:-12]
        self.output.write_bytes(data)
        report_path = self.root / "worker_report.json"
        report = {"prompt_id": "mock-prompt", "output_node": "13",
                  "status": "UNRESOLVED", "outputs": [], "errors": []}
        graph = {"13": {"class_type": "SaveImage"}}
        with mock.patch.object(execution, "request_json", return_value={"mock-prompt": self.record}),                 mock.patch.object(execution.urllib.request, "urlopen", return_value=io.BytesIO(data)):
            code = execution.track(report_path, report, self.comfy, time.monotonic() + 5, graph)
        self.assertEqual(code, 1)
        stored = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual(stored["status"], "FAILED")
        self.assertEqual(stored["outputs"], [])
        self.assertIn("artifact verification", stored["errors"][0])


if __name__ == "__main__":
    unittest.main()
