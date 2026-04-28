import tempfile
import unittest
from pathlib import Path

from shared.errors import ValidationError
from validation.file_validators import (
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


if __name__ == "__main__":
    unittest.main()
