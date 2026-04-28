import unittest

from domain.media_info import AudioStreamInfo, MediaInfo, VideoStreamInfo
from shared.errors import ValidationError
from validation.media_validators import (
    are_concat_streams_compatible,
    build_concat_compatibility_report,
    validate_trim_end_within_duration,
)


def _make_media(
    path: str = "test.mp4",
    duration: float | None = 60.0,
    format_name: str = "mov,mp4,m4a,3gp,3g2,mj2",
    v_codec: str = "h264",
    width: int = 1920,
    height: int = 1080,
    fps: float = 29.97,
    a_codec: str = "aac",
) -> MediaInfo:
    return MediaInfo(
        path=path,
        duration_seconds=duration,
        format_name=format_name,
        video=VideoStreamInfo(codec_name=v_codec, width=width, height=height, fps=fps),
        audio=AudioStreamInfo(codec_name=a_codec),
    )


class TestValidateTrimEndWithinDuration(unittest.TestCase):
    def test_within_duration(self):
        media = _make_media(duration=120.0)
        validate_trim_end_within_duration(60, media)

    def test_exceeds_duration(self):
        media = _make_media(duration=60.0)
        with self.assertRaises(ValidationError):
            validate_trim_end_within_duration(90, media)

    def test_unknown_duration_passes(self):
        media = _make_media(duration=None)
        validate_trim_end_within_duration(9999, media)


class TestAreConcatStreamsCompatible(unittest.TestCase):
    def test_single_file(self):
        self.assertTrue(are_concat_streams_compatible([_make_media()]))

    def test_identical_files(self):
        a = _make_media()
        b = _make_media(path="test2.mp4")
        self.assertTrue(are_concat_streams_compatible([a, b]))

    def test_different_codec(self):
        a = _make_media(v_codec="h264")
        b = _make_media(v_codec="hevc")
        self.assertFalse(are_concat_streams_compatible([a, b]))

    def test_different_resolution(self):
        a = _make_media(width=1920, height=1080)
        b = _make_media(width=1280, height=720)
        self.assertFalse(are_concat_streams_compatible([a, b]))

    def test_different_fps(self):
        a = _make_media(fps=29.97)
        b = _make_media(fps=24.0)
        self.assertFalse(are_concat_streams_compatible([a, b]))

    def test_different_audio_codec(self):
        a = _make_media(a_codec="aac")
        b = _make_media(a_codec="mp3")
        self.assertFalse(are_concat_streams_compatible([a, b]))

    def test_different_container(self):
        a = _make_media(format_name="mov,mp4,m4a,3gp,3g2,mj2")
        b = _make_media(format_name="matroska,webm")
        self.assertFalse(are_concat_streams_compatible([a, b]))

    def test_one_has_video_other_not(self):
        a = _make_media()
        b = MediaInfo(
            path="b.mp4",
            duration_seconds=60.0,
            format_name="mov,mp4,m4a,3gp,3g2,mj2",
            video=None,
            audio=AudioStreamInfo(codec_name="aac"),
        )
        self.assertFalse(are_concat_streams_compatible([a, b]))

    def test_one_has_audio_other_not(self):
        a = _make_media()
        b = MediaInfo(
            path="b.mp4",
            duration_seconds=60.0,
            format_name="mov,mp4,m4a,3gp,3g2,mj2",
            video=VideoStreamInfo(codec_name="h264", width=1920, height=1080, fps=29.97),
            audio=None,
        )
        self.assertFalse(are_concat_streams_compatible([a, b]))

    def test_three_files_all_compatible(self):
        files = [_make_media(path=f"{i}.mp4") for i in range(3)]
        self.assertTrue(are_concat_streams_compatible(files))

    def test_three_files_third_incompatible(self):
        a = _make_media(path="1.mp4")
        b = _make_media(path="2.mp4")
        c = _make_media(path="3.mp4", v_codec="hevc")
        self.assertFalse(are_concat_streams_compatible([a, b, c]))


class TestBuildConcatCompatibilityReport(unittest.TestCase):
    def test_compatible_report_contains_copy(self):
        files = [_make_media(), _make_media(path="b.mp4")]
        report = build_concat_compatibility_report(files)
        self.assertIn("互換あり", report)
        self.assertIn("copy", report)

    def test_incompatible_report_contains_reencode(self):
        a = _make_media(v_codec="h264")
        b = _make_media(v_codec="hevc")
        report = build_concat_compatibility_report([a, b])
        self.assertIn("互換なし", report)
        self.assertIn("再エンコード", report)


if __name__ == "__main__":
    unittest.main()
