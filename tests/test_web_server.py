import json
import unittest

from ui.web.server import _build_command, app
from ffmpeg.commands import (
    build_compress_command,
    build_fps_command,
    build_resize_command,
    build_volume_command,
)
from domain.trim_range import TrimRange
from ffmpeg.commands import build_trim_command
from shared.errors import ValidationError


class TestPreviewEndpoint(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_fps_preview_returns_command(self):
        res = self.client.post(
            "/api/preview",
            data=json.dumps({
                "operation": "fps",
                "params": {"input_file": "in.mp4", "fps": "30", "output_file": "out.mp4"},
            }),
            content_type="application/json",
        )
        body = res.get_json()
        self.assertTrue(body["ok"])
        self.assertIn("ffmpeg", body["command"])
        self.assertIn("fps=30", body["command"])

    def test_unknown_operation_returns_error(self):
        res = self.client.post(
            "/api/preview",
            data=json.dumps({"operation": "invalid_op", "params": {}}),
            content_type="application/json",
        )
        body = res.get_json()
        self.assertFalse(body["ok"])
        self.assertIn("error", body)

    def test_resize_preview(self):
        res = self.client.post(
            "/api/preview",
            data=json.dumps({
                "operation": "resize",
                "params": {"input_file": "in.mp4", "width": "1280", "height": "720", "output_file": "out.mp4"},
            }),
            content_type="application/json",
        )
        body = res.get_json()
        self.assertTrue(body["ok"])
        self.assertIn("1280:720", body["command"])

    def test_probe_missing_file_returns_error(self):
        res = self.client.post(
            "/api/probe",
            data=json.dumps({"file_path": "/nonexistent/file.mp4"}),
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 400)
        body = res.get_json()
        self.assertFalse(body["ok"])


class TestBuildCommand(unittest.TestCase):
    def test_fps(self):
        cmd = _build_command("fps", {"input_file": "in.mp4", "fps": "30", "output_file": "out.mp4"})
        expected = build_fps_command("in.mp4", "out.mp4", 30.0)
        self.assertEqual(cmd, expected)

    def test_resize(self):
        cmd = _build_command("resize", {"input_file": "in.mp4", "width": "1280", "height": "720", "output_file": "out.mp4"})
        expected = build_resize_command("in.mp4", "out.mp4", 1280, 720)
        self.assertEqual(cmd, expected)

    def test_trim(self):
        cmd = _build_command("trim", {"input_file": "in.mp4", "start_time": "10", "end_time": "30", "output_file": "out.mp4"})
        expected = build_trim_command("in.mp4", "out.mp4", TrimRange.create(10, 30))
        self.assertEqual(cmd, expected)

    def test_volume(self):
        cmd = _build_command("volume", {"input_file": "in.mp4", "volume_level": "1.5", "output_file": "out.mp4"})
        expected = build_volume_command("in.mp4", "out.mp4", 1.5)
        self.assertEqual(cmd, expected)

    def test_compress(self):
        cmd = _build_command("compress", {"input_file": "in.mp4", "crf": "23", "output_file": "out.mp4"})
        expected = build_compress_command("in.mp4", "out.mp4", 23)
        self.assertEqual(cmd, expected)

    def test_unknown_operation_raises(self):
        with self.assertRaises(ValueError):
            _build_command("nonexistent", {})


if __name__ == "__main__":
    unittest.main()
