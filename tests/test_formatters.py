import unittest

from domain.media_info import AudioStreamInfo, MediaInfo, VideoStreamInfo
from shared.formatters import format_media_info_summary, format_seconds_to_hhmmss


class TestFormatSecondsToHhmmss(unittest.TestCase):
    def test_zero(self):
        self.assertEqual(format_seconds_to_hhmmss(0), "00:00:00")

    def test_seconds_only(self):
        self.assertEqual(format_seconds_to_hhmmss(45), "00:00:45")

    def test_minutes_and_seconds(self):
        self.assertEqual(format_seconds_to_hhmmss(90), "00:01:30")

    def test_hours(self):
        self.assertEqual(format_seconds_to_hhmmss(3661), "01:01:01")

    def test_none(self):
        self.assertEqual(format_seconds_to_hhmmss(None), "不明")

    def test_float(self):
        self.assertEqual(format_seconds_to_hhmmss(90.7), "00:01:30")


class TestFormatMediaInfoSummary(unittest.TestCase):
    def test_full_info(self):
        media = MediaInfo(
            path="test.mp4",
            duration_seconds=120.0,
            format_name="mov,mp4",
            video=VideoStreamInfo(codec_name="h264", width=1920, height=1080, fps=29.97),
            audio=AudioStreamInfo(codec_name="aac"),
        )
        result = format_media_info_summary(media)
        self.assertIn("test.mp4", result)
        self.assertIn("00:02:00", result)
        self.assertIn("h264", result)
        self.assertIn("1920x1080", result)
        self.assertIn("aac", result)

    def test_no_video(self):
        media = MediaInfo(
            path="audio.mp3",
            duration_seconds=60.0,
            format_name="mp3",
            video=None,
            audio=AudioStreamInfo(codec_name="mp3"),
        )
        result = format_media_info_summary(media)
        self.assertNotIn("映像", result)
        self.assertIn("mp3", result)

    def test_no_audio(self):
        media = MediaInfo(
            path="video.mp4",
            duration_seconds=60.0,
            format_name="mov,mp4",
            video=VideoStreamInfo(codec_name="h264", width=1920, height=1080, fps=30.0),
            audio=None,
        )
        result = format_media_info_summary(media)
        self.assertNotIn("音声", result)
        self.assertIn("h264", result)

    def test_unknown_values(self):
        media = MediaInfo(
            path="test.mp4",
            duration_seconds=None,
            format_name=None,
            video=VideoStreamInfo(codec_name=None, width=None, height=None, fps=None),
            audio=AudioStreamInfo(codec_name=None),
        )
        result = format_media_info_summary(media)
        self.assertIn("不明", result)


if __name__ == "__main__":
    unittest.main()
