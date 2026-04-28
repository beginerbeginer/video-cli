import unittest
from unittest.mock import patch

from domain.media_info import AudioStreamInfo, MediaInfo, VideoStreamInfo
from ffmpeg.probe import probe_media_info


class TestProbe(unittest.TestCase):
    @patch("ffmpeg.probe.run_ffprobe")
    def test_probe_media_info_delegates_to_parser(self, mock_run_ffprobe):
        mock_run_ffprobe.return_value = {
            "format": {"duration": "120.5", "format_name": "mov,mp4"},
            "streams": [
                {
                    "codec_type": "video",
                    "codec_name": "h264",
                    "width": 1920,
                    "height": 1080,
                    "avg_frame_rate": "30/1",
                },
                {"codec_type": "audio", "codec_name": "aac"},
            ],
        }

        result = probe_media_info("test.mp4")

        self.assertEqual(
            result,
            MediaInfo(
                path="test.mp4",
                duration_seconds=120.5,
                format_name="mov,mp4",
                video=VideoStreamInfo("h264", 1920, 1080, 30.0),
                audio=AudioStreamInfo("aac"),
            ),
        )
        mock_run_ffprobe.assert_called_once_with("test.mp4")


if __name__ == "__main__":
    unittest.main()
