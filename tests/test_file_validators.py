import tempfile
import unittest
from pathlib import Path

from shared.errors import ValidationError
from validation.file_validators import (
    validate_audio_output_extension,
    validate_compress_output_extension,
    validate_different_extension,
    validate_gif_output_extension,
    validate_image_output_extension,
    validate_input_file_exists,
    validate_output_directory_exists,
    validate_video_file_extension,
)


class TestFileValidators(unittest.TestCase):
    def test_validate_input_file_exists_passes_for_existing_file(self):
        with tempfile.NamedTemporaryFile() as tmp:
            validate_input_file_exists(tmp.name)

    def test_validate_input_file_exists_raises_for_missing_file(self):
        with self.assertRaises(ValidationError):
            validate_input_file_exists("not_found.mp4")

    def test_validate_video_file_extension_passes(self):
        validate_video_file_extension("movie.mp4")

    def test_validate_video_file_extension_raises_for_unsupported_extension(self):
        with self.assertRaises(ValidationError):
            validate_video_file_extension("movie.txt")

    def test_validate_output_directory_exists_passes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = str(Path(tmpdir) / "out.mp4")
            validate_output_directory_exists(output_path)

    def test_validate_output_directory_exists_raises_for_missing_directory(self):
        with self.assertRaises(ValidationError):
            validate_output_directory_exists("/not/existing/dir/out.mp4")


class TestValidateAudioOutputExtension(unittest.TestCase):
    def test_mp3_passes(self):
        validate_audio_output_extension("output.mp3")

    def test_aac_passes(self):
        validate_audio_output_extension("output.aac")

    def test_wav_passes(self):
        validate_audio_output_extension("output.wav")

    def test_m4a_passes(self):
        validate_audio_output_extension("output.m4a")

    def test_unsupported_raises(self):
        with self.assertRaises(ValidationError):
            validate_audio_output_extension("output.mp4")

    def test_txt_raises(self):
        with self.assertRaises(ValidationError):
            validate_audio_output_extension("output.txt")


class TestValidateGifOutputExtension(unittest.TestCase):
    def test_gif_passes(self):
        validate_gif_output_extension("output.gif")

    def test_mp4_raises(self):
        with self.assertRaises(ValidationError):
            validate_gif_output_extension("output.mp4")

    def test_jpg_raises(self):
        with self.assertRaises(ValidationError):
            validate_gif_output_extension("output.jpg")


class TestValidateImageOutputExtension(unittest.TestCase):
    def test_jpg_passes(self):
        validate_image_output_extension("output.jpg")

    def test_jpeg_passes(self):
        validate_image_output_extension("output.jpeg")

    def test_png_passes(self):
        validate_image_output_extension("output.png")

    def test_mp4_raises(self):
        with self.assertRaises(ValidationError):
            validate_image_output_extension("output.mp4")

    def test_txt_raises(self):
        with self.assertRaises(ValidationError):
            validate_image_output_extension("output.txt")


class TestValidateDifferentExtension(unittest.TestCase):
    def test_different_extensions_passes(self):
        validate_different_extension("input.mov", "output.mp4")

    def test_same_extension_raises(self):
        with self.assertRaises(ValidationError):
            validate_different_extension("input.mp4", "output.mp4")

    def test_case_insensitive(self):
        with self.assertRaises(ValidationError):
            validate_different_extension("input.MP4", "output.mp4")


class TestValidateCompressOutputExtension(unittest.TestCase):
    def test_mp4_passes(self):
        validate_compress_output_extension("out.mp4")

    def test_mov_passes(self):
        validate_compress_output_extension("out.mov")

    def test_mkv_passes(self):
        validate_compress_output_extension("out.mkv")

    def test_webm_raises(self):
        with self.assertRaises(ValidationError):
            validate_compress_output_extension("out.webm")

    def test_unsupported_raises(self):
        with self.assertRaises(ValidationError):
            validate_compress_output_extension("out.avi")


if __name__ == "__main__":
    unittest.main()
