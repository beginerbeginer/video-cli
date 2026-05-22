import unittest

from domain.trim_range import TrimRange
from ffmpeg.commands import (
    build_audio_extract_command,
    build_concat_copy_command,
    build_concat_reencode_command,
    build_gif_command,
    build_resize_command,
    build_thumbnail_command,
    build_trim_command,
    build_volume_command,
)


class TestBuildTrimCommand(unittest.TestCase):
    def test_basic(self):
        command = build_trim_command(
            input_file="in.mp4",
            output_file="out.mp4",
            trim_range=TrimRange.create(10, 20),
        )
        self.assertEqual(
            command,
            [
                "ffmpeg",
                "-y",
                "-ss",
                "10",
                "-i",
                "in.mp4",
                "-t",
                "10",
                "-c:v",
                "libx264",
                "-c:a",
                "aac",
                "out.mp4",
            ],
        )


class TestBuildResizeCommand(unittest.TestCase):
    def test_basic(self):
        command = build_resize_command("in.mp4", "out.mp4", 1280, 720)
        self.assertEqual(
            command,
            [
                "ffmpeg",
                "-y",
                "-i",
                "in.mp4",
                "-vf",
                "scale=1280:720",
                "-c:v",
                "libx264",
                "-c:a",
                "aac",
                "out.mp4",
            ],
        )


class TestBuildConcatCopyCommand(unittest.TestCase):
    def test_basic(self):
        command = build_concat_copy_command("list.txt", "out.mp4")
        self.assertEqual(
            command,
            [
                "ffmpeg",
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                "list.txt",
                "-c",
                "copy",
                "out.mp4",
            ],
        )


class TestBuildConcatReencodeCommand(unittest.TestCase):
    def test_basic(self):
        command = build_concat_reencode_command("list.txt", "out.mp4")
        self.assertEqual(
            command,
            [
                "ffmpeg",
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                "list.txt",
                "-c:v",
                "libx264",
                "-c:a",
                "aac",
                "out.mp4",
            ],
        )


class TestBuildVolumeCommand(unittest.TestCase):
    def test_basic(self):
        command = build_volume_command("in.mp4", "out.mp4", 1.5)
        self.assertEqual(
            command,
            [
                "ffmpeg",
                "-y",
                "-i",
                "in.mp4",
                "-filter:a",
                "volume=1.5",
                "-c:v",
                "copy",
                "out.mp4",
            ],
        )

    def test_volume_one_keeps_original(self):
        command = build_volume_command("in.mp4", "out.mp4", 1.0)
        self.assertIn("volume=1.0", command)

    def test_video_stream_is_copied(self):
        command = build_volume_command("in.mp4", "out.mp4", 2.0)
        copy_idx = command.index("copy")
        self.assertEqual(command[copy_idx - 1], "-c:v")


class TestBuildGifCommand(unittest.TestCase):
    def test_basic(self):
        command = build_gif_command("in.mp4", "out.gif", 10, 480)
        self.assertEqual(
            command,
            [
                "ffmpeg",
                "-y",
                "-i",
                "in.mp4",
                "-vf",
                "fps=10,scale=480:-1:flags=lanczos",
                "out.gif",
            ],
        )

    def test_filter_contains_fps(self):
        command = build_gif_command("in.mp4", "out.gif", 15, 320)
        vf_idx = command.index("-vf")
        self.assertIn("fps=15", command[vf_idx + 1])

    def test_filter_contains_scale(self):
        command = build_gif_command("in.mp4", "out.gif", 10, 640)
        vf_idx = command.index("-vf")
        self.assertIn("scale=640:-1", command[vf_idx + 1])


class TestBuildThumbnailCommand(unittest.TestCase):
    def test_basic(self):
        command = build_thumbnail_command("in.mp4", "out.jpg", 10)
        self.assertEqual(
            command,
            [
                "ffmpeg",
                "-y",
                "-ss",
                "10",
                "-i",
                "in.mp4",
                "-vframes",
                "1",
                "out.jpg",
            ],
        )

    def test_timestamp_zero(self):
        command = build_thumbnail_command("in.mp4", "out.jpg", 0)
        self.assertIn("0", command)

    def test_single_frame(self):
        command = build_thumbnail_command("in.mp4", "out.png", 5)
        vframes_idx = command.index("-vframes")
        self.assertEqual(command[vframes_idx + 1], "1")


class TestBuildAudioExtractCommand(unittest.TestCase):
    def test_basic(self):
        command = build_audio_extract_command("in.mp4", "out.mp3")
        self.assertEqual(
            command,
            [
                "ffmpeg",
                "-y",
                "-i",
                "in.mp4",
                "-vn",
                "-c:a",
                "copy",
                "out.mp3",
            ],
        )

    def test_no_video_stream(self):
        command = build_audio_extract_command("in.mp4", "out.aac")
        self.assertIn("-vn", command)

    def test_audio_copied_not_reencoded(self):
        command = build_audio_extract_command("in.mp4", "out.mp3")
        copy_idx = command.index("copy")
        self.assertEqual(command[copy_idx - 1], "-c:a")


if __name__ == "__main__":
    unittest.main()
