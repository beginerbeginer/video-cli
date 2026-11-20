import unittest

from shared.errors import ValidationError
from tests.form_test_support import FormWorkspace
from usecases.form_validation import form_field, require_field, validate_output_path, validate_video_input_path


class TestFormField(unittest.TestCase):
    def test_tags_error_without_field(self):
        with self.assertRaises(ValidationError) as ctx:
            with form_field("crf_raw"):
                raise ValidationError("CRF 値 は整数で入力してください。")
        self.assertEqual(ctx.exception.field, "crf_raw")
        self.assertEqual(str(ctx.exception), "CRF 値 は整数で入力してください。")

    def test_keeps_field_already_set_by_inner_check(self):
        with self.assertRaises(ValidationError) as ctx:
            with form_field("outer"):
                raise ValidationError("msg", field="inner")
        self.assertEqual(ctx.exception.field, "inner")

    def test_does_nothing_when_no_error(self):
        with form_field("x"):
            value = 1
        self.assertEqual(value, 1)


class TestRequireField(unittest.TestCase):
    def test_returns_value(self):
        self.assertEqual(require_field("10", "開始時間", "start_raw"), "10")

    def test_blank_raises_with_field(self):
        with self.assertRaises(ValidationError) as ctx:
            require_field("  ", "開始時間", "start_raw")
        self.assertEqual(ctx.exception.field, "start_raw")
        self.assertEqual(str(ctx.exception), "開始時間は空にできません。")


class TestValidateVideoInputPath(unittest.TestCase):
    def setUp(self):
        self.ws = FormWorkspace()
        self.addCleanup(self.ws.cleanup)

    def test_accepts_existing_video(self):
        validate_video_input_path(self.ws.input_file)

    def test_errors_are_tagged_input_file(self):
        txt = self.ws.root / "in.txt"
        txt.write_text("")
        for path in ["", self.ws.missing_input, str(txt)]:
            with self.subTest(path=path):
                with self.assertRaises(ValidationError) as ctx:
                    validate_video_input_path(path)
                self.assertEqual(ctx.exception.field, "input_file")


class TestValidateOutputPath(unittest.TestCase):
    def setUp(self):
        self.ws = FormWorkspace()
        self.addCleanup(self.ws.cleanup)

    def test_accepts_existing_directory(self):
        validate_output_path(self.ws.output())

    def test_errors_are_tagged_output_file(self):
        for path in [" ", self.ws.output_in_missing_dir]:
            with self.subTest(path=path):
                with self.assertRaises(ValidationError) as ctx:
                    validate_output_path(path)
                self.assertEqual(ctx.exception.field, "output_file")


if __name__ == "__main__":
    unittest.main()
