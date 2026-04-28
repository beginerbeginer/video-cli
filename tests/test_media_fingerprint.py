import unittest

from domain.media_fingerprint import MediaFingerprint
from domain.media_info import AudioStreamInfo, MediaInfo, VideoStreamInfo


class TestMediaFingerprint(unittest.TestCase):
    def test_same_media_produces_same_fingerprint(self):
        a = MediaInfo(
            path="a.mp4",
            duration_seconds=10.0,
            format_name="mov,mp4",
            video=VideoStreamInfo("h264", 1920, 1080, 29.97),
            audio=AudioStreamInfo("aac"),
        )
        b = MediaInfo(
            path="b.mp4",
            duration_seconds=20.0,
            format_name="mov,mp4",
            video=VideoStreamInfo("h264", 1920, 1080, 29.97),
            audio=AudioStreamInfo("aac"),
        )

        self.assertEqual(
            MediaFingerprint.from_media_info(a),
            MediaFingerprint.from_media_info(b),
        )


if __name__ == "__main__":
    unittest.main()
