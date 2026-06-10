import unittest
from pathlib import Path

from domain.trim_range import TrimRange
from ffmpeg.commands import (
    build_audio_extract_command,
    build_compress_command,
    build_concat_copy_command,
    build_concat_reencode_command,
    build_convert_command,
    build_crop_command,
    build_fps_command,
    build_gif_command,
    build_mute_command,
    build_resize_command,
    build_rotate_command,
    build_speed_command,
    build_thumbnail_command,
    build_trim_command,
    build_volume_command,
    create_concat_list_file,
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


class TestBuildSpeedCommand(unittest.TestCase):
    def test_double_speed(self):
        command = build_speed_command("in.mp4", "out.mp4", 2.0)
        self.assertEqual(
            command,
            [
                "ffmpeg",
                "-y",
                "-i",
                "in.mp4",
                "-vf",
                "setpts=0.5*PTS",
                "-filter:a",
                "atempo=2.0",
                "-c:v",
                "libx264",
                "-c:a",
                "aac",
                "out.mp4",
            ],
        )

    def test_half_speed(self):
        command = build_speed_command("in.mp4", "out.mp4", 0.5)
        self.assertIn("setpts=2.0*PTS", command)
        self.assertIn("atempo=0.5", command)

    def test_4x_speed_uses_chained_atempo(self):
        # 4倍速は atempo 2段連結: atempo=2.0,atempo=2.0
        command = build_speed_command("in.mp4", "out.mp4", 4.0)
        atempo_filter = command[command.index("-filter:a") + 1]
        self.assertEqual(atempo_filter, "atempo=2.0,atempo=2.0")

    def test_025x_speed_uses_chained_atempo(self):
        # 0.25倍速は atempo 2段連結: atempo=0.5,atempo=0.5
        command = build_speed_command("in.mp4", "out.mp4", 0.25)
        atempo_filter = command[command.index("-filter:a") + 1]
        self.assertEqual(atempo_filter, "atempo=0.5,atempo=0.5")

    def test_normal_speed(self):
        command = build_speed_command("in.mp4", "out.mp4", 1.0)
        self.assertIn("setpts=1.0*PTS", command)
        self.assertIn("atempo=1.0", command)


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


class TestBuildConvertCommand(unittest.TestCase):
    def test_basic(self):
        command = build_convert_command("in.mov", "out.mp4")
        self.assertEqual(
            command,
            ["ffmpeg", "-y", "-i", "in.mov", "-c", "copy", "out.mp4"],
        )

    def test_no_reencode(self):
        command = build_convert_command("in.mov", "out.mp4")
        copy_idx = command.index("copy")
        self.assertEqual(command[copy_idx - 1], "-c")


class TestBuildMuteCommand(unittest.TestCase):
    def test_basic(self):
        command = build_mute_command("in.mp4", "out.mp4")
        self.assertEqual(
            command,
            ["ffmpeg", "-y", "-i", "in.mp4", "-an", "-c:v", "copy", "out.mp4"],
        )

    def test_no_audio_flag(self):
        command = build_mute_command("in.mp4", "out.mp4")
        self.assertIn("-an", command)

    def test_video_stream_copied(self):
        command = build_mute_command("in.mp4", "out.mp4")
        copy_idx = command.index("copy")
        self.assertEqual(command[copy_idx - 1], "-c:v")

    def test_video_stream_preserved(self):
        command = build_mute_command("in.mp4", "out.mp4")
        self.assertNotIn("-vn", command)


class TestBuildCropCommand(unittest.TestCase):
    def test_basic(self):
        command = build_crop_command("in.mp4", "out.mp4", width=640, height=360, x=0, y=0)
        self.assertEqual(
            command,
            ["ffmpeg", "-y", "-i", "in.mp4", "-vf", "crop=640:360:0:0", "-c:v", "libx264", "-c:a", "aac", "out.mp4"],
        )

    def test_vf_filter_format(self):
        command = build_crop_command("in.mp4", "out.mp4", width=320, height=240, x=100, y=50)
        vf_idx = command.index("-vf")
        self.assertEqual(command[vf_idx + 1], "crop=320:240:100:50")

    def test_offset_zero(self):
        command = build_crop_command("in.mp4", "out.mp4", width=1280, height=720, x=0, y=0)
        self.assertIn("crop=1280:720:0:0", command)


class TestBuildRotateCommand(unittest.TestCase):
    def test_right90(self):
        command = build_rotate_command("in.mp4", "out.mp4", "right90")
        self.assertEqual(
            command,
            ["ffmpeg", "-y", "-i", "in.mp4", "-vf", "transpose=1", "-c:v", "libx264", "-c:a", "aac", "out.mp4"],
        )

    def test_left90(self):
        command = build_rotate_command("in.mp4", "out.mp4", "left90")
        vf_idx = command.index("-vf")
        self.assertEqual(command[vf_idx + 1], "transpose=2")

    def test_rot180(self):
        command = build_rotate_command("in.mp4", "out.mp4", "rot180")
        vf_idx = command.index("-vf")
        self.assertEqual(command[vf_idx + 1], "transpose=1,transpose=1")

    def test_hflip(self):
        command = build_rotate_command("in.mp4", "out.mp4", "hflip")
        vf_idx = command.index("-vf")
        self.assertEqual(command[vf_idx + 1], "hflip")

    def test_vflip(self):
        command = build_rotate_command("in.mp4", "out.mp4", "vflip")
        vf_idx = command.index("-vf")
        self.assertEqual(command[vf_idx + 1], "vflip")


class TestCreateConcatListFile(unittest.TestCase):
    def test_yields_path_with_correct_content(self):
        input_files = ["/tmp/a.mp4", "/tmp/b.mp4"]
        with create_concat_list_file(input_files) as path:
            content = Path(path).read_text()
        self.assertIn("a.mp4", content)
        self.assertIn("b.mp4", content)

    def test_deletes_file_after_with_block(self):
        input_files = ["/tmp/a.mp4"]
        with create_concat_list_file(input_files) as path:
            captured_path = path
        self.assertFalse(Path(captured_path).exists())

    def test_deletes_file_even_when_exception_raised(self):
        input_files = ["/tmp/a.mp4"]
        captured_path = None
        with self.assertRaises(RuntimeError):
            with create_concat_list_file(input_files) as path:
                captured_path = path
                raise RuntimeError("test error")
        self.assertFalse(Path(captured_path).exists())

    def test_deletes_file_when_write_raises(self):
        import tempfile
        from unittest.mock import MagicMock, patch

        real_tmp = tempfile.NamedTemporaryFile(delete=False)
        real_tmp.close()
        real_tmp_name = real_tmp.name
        self.addCleanup(Path(real_tmp_name).unlink, missing_ok=True)

        mock_file = MagicMock()
        mock_file.__enter__ = MagicMock(return_value=mock_file)
        mock_file.__exit__ = MagicMock(return_value=False)
        mock_file.write.side_effect = OSError("disk full")
        mock_file.name = real_tmp_name

        with self.assertRaises(OSError):
            with patch("ffmpeg.commands.NamedTemporaryFile", return_value=mock_file):
                with create_concat_list_file(["/tmp/a.mp4"]):
                    pass

        self.assertFalse(Path(real_tmp_name).exists())

    def test_each_line_has_ffmpeg_file_entry_format(self):
        with create_concat_list_file(["/tmp/a.mp4", "/tmp/b.mp4"]) as path:
            content = Path(path).read_text()
        lines = content.strip().split("\n")
        self.assertEqual(len(lines), 2)
        for line in lines:
            self.assertRegex(line, r"^file '.*'$")

    def test_single_quote_in_path_is_escaped(self):
        with create_concat_list_file(["/tmp/it's.mp4"]) as path:
            content = Path(path).read_text()
        self.assertIn(r"'\''" , content)


class TestBuildCompressCommand(unittest.TestCase):
    def test_command_starts_with_ffmpeg(self):
        command = build_compress_command("in.mp4", "out.mp4", crf=23)
        self.assertEqual(command[0], "ffmpeg")

    def test_uses_libx264_codec(self):
        command = build_compress_command("in.mp4", "out.mp4", crf=23)
        self.assertIn("libx264", command)

    def test_default_crf_is_23(self):
        command = build_compress_command("in.mp4", "out.mp4")
        crf_idx = command.index("-crf")
        self.assertEqual(command[crf_idx + 1], "23")

    def test_custom_crf_value(self):
        command = build_compress_command("in.mp4", "out.mp4", crf=18)
        crf_idx = command.index("-crf")
        self.assertEqual(command[crf_idx + 1], "18")

    def test_audio_is_transcoded_to_aac(self):
        command = build_compress_command("in.mp4", "out.mp4", crf=23)
        ca_idx = command.index("-c:a")
        self.assertEqual(command[ca_idx + 1], "aac")

    def test_includes_input_and_output_files(self):
        command = build_compress_command("in.mp4", "out.mp4", crf=23)
        self.assertIn("in.mp4", command)
        self.assertIn("out.mp4", command)


class TestBuildFpsCommand(unittest.TestCase):
    def test_basic(self):
        command = build_fps_command("in.mp4", "out.mp4", fps=30.0)
        self.assertEqual(
            command,
            ["ffmpeg", "-y", "-i", "in.mp4", "-vf", "fps=30", "-c:a", "copy", "out.mp4"],
        )

    def test_decimal_fps(self):
        command = build_fps_command("in.mp4", "out.mp4", fps=23.976)
        vf_idx = command.index("-vf")
        self.assertEqual(command[vf_idx + 1], "fps=23.976")

    def test_webm_output_uses_libopus(self):
        command = build_fps_command("in.mp4", "out.webm", fps=30.0)
        ca_idx = command.index("-c:a")
        self.assertEqual(command[ca_idx + 1], "libopus")

    def test_mp4_output_uses_copy(self):
        command = build_fps_command("in.mp4", "out.mp4", fps=30.0)
        ca_idx = command.index("-c:a")
        self.assertEqual(command[ca_idx + 1], "copy")

    def test_webm_input_mp4_output_uses_aac(self):
        command = build_fps_command("in.webm", "out.mp4", fps=30.0)
        ca_idx = command.index("-c:a")
        self.assertEqual(command[ca_idx + 1], "aac")


if __name__ == "__main__":
    unittest.main()
