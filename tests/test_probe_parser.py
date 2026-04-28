import unittest

from ffmpeg.probe_parser import (
    build_media_info,
    extract_audio_info,
    extract_duration,
    extract_video_info,
    find_stream,
    parse_fps,
    split_ffprobe_output,
)


class TestParseFps(unittest.TestCase):
    def test_fraction(self):
        self.assertAlmostEqual(parse_fps("30000/1001"), 29.97, places=1)

    def test_integer_fraction(self):
        self.assertAlmostEqual(parse_fps("30/1"), 30.0)

    def test_zero_over_zero(self):
        self.assertIsNone(parse_fps("0/0"))

    def test_none(self):
        self.assertIsNone(parse_fps(None))

    def test_invalid(self):
        self.assertIsNone(parse_fps("not_a_number"))


class TestFindStream(unittest.TestCase):
    def test_find_video(self):
        streams = [
            {"codec_type": "audio", "codec_name": "aac"},
            {"codec_type": "video", "codec_name": "h264"},
        ]
        result = find_stream(streams, "video")
        self.assertEqual(result["codec_name"], "h264")

    def test_not_found(self):
        streams = [{"codec_type": "audio", "codec_name": "aac"}]
        self.assertIsNone(find_stream(streams, "video"))


class TestExtractVideoInfo(unittest.TestCase):
    def test_valid_stream(self):
        stream = {
            "codec_type": "video",
            "codec_name": "h264",
            "width": 1920,
            "height": 1080,
            "avg_frame_rate": "30/1",
        }
        result = extract_video_info(stream)
        self.assertIsNotNone(result)
        self.assertEqual(result.codec_name, "h264")
        self.assertEqual(result.width, 1920)
        self.assertEqual(result.height, 1080)
        self.assertAlmostEqual(result.fps, 30.0)

    def test_none_input(self):
        self.assertIsNone(extract_video_info(None))


class TestExtractAudioInfo(unittest.TestCase):
    def test_valid_stream(self):
        stream = {"codec_type": "audio", "codec_name": "aac"}
        result = extract_audio_info(stream)
        self.assertIsNotNone(result)
        self.assertEqual(result.codec_name, "aac")

    def test_none_input(self):
        self.assertIsNone(extract_audio_info(None))


class TestExtractDuration(unittest.TestCase):
    def test_present(self):
        self.assertAlmostEqual(extract_duration({"duration": "120.5"}), 120.5)

    def test_missing(self):
        self.assertIsNone(extract_duration({}))


class TestSplitFfprobeOutput(unittest.TestCase):
    def test_split_output(self):
        data = {"format": {"duration": "120.5"}, "streams": [{"codec_type": "video"}]}
        format_info, streams = split_ffprobe_output(data)
        self.assertEqual(format_info, {"duration": "120.5"})
        self.assertEqual(streams, [{"codec_type": "video"}])


class TestBuildMediaInfo(unittest.TestCase):
    def test_build_media_info(self):
        data = {
            "format": {"duration": "120.5", "format_name": "mov,mp4"},
            "streams": [
                {
                    "codec_type": "video",
                    "codec_name": "h264",
                    "width": 1920,
                    "height": 1080,
                    "avg_frame_rate": "30/1",
                },
                {
                    "codec_type": "audio",
                    "codec_name": "aac",
                },
            ],
        }
        media = build_media_info("test.mp4", data)
        self.assertEqual(media.path, "test.mp4")
        self.assertEqual(media.format_name, "mov,mp4")
        self.assertAlmostEqual(media.duration_seconds, 120.5)
        self.assertEqual(media.video.codec_name, "h264")
        self.assertEqual(media.audio.codec_name, "aac")


if __name__ == "__main__":
    unittest.main()
