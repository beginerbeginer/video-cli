import unittest

from shared.errors import ValidationError
from tests.form_test_support import FormWorkspace
from usecases.form_validation import form_field, require_field, validate_output_path, validate_video_input_path


class TestFormField(unittest.TestCase):
    def test_fieldなしのエラーが起きるとfieldを付けて投げ直す(self):
        # Act
        with self.assertRaises(ValidationError) as ctx:
            with form_field("crf_raw"):
                raise ValidationError("CRF 値 は整数で入力してください。")

        # Assert
        self.assertEqual(ctx.exception.field, "crf_raw")
        self.assertEqual(str(ctx.exception), "CRF 値 は整数で入力してください。")

    def test_内側ですでにfieldが付いていればそのまま投げる(self):
        # Act
        with self.assertRaises(ValidationError) as ctx:
            with form_field("outer"):
                raise ValidationError("msg", field="inner")

        # Assert
        self.assertEqual(ctx.exception.field, "inner")

    def test_エラーが起きなければ何もしない(self):
        # Act
        with form_field("x"):
            value = 1

        # Assert
        self.assertEqual(value, 1)


class TestRequireField(unittest.TestCase):
    def test_空でなければ値をそのまま返す(self):
        # Act
        value = require_field("10", "開始時間", "start_raw")

        # Assert
        self.assertEqual(value, "10")

    def test_空白だけだとfield付きのエラーになる(self):
        # Act
        with self.assertRaises(ValidationError) as ctx:
            require_field("  ", "開始時間", "start_raw")

        # Assert
        self.assertEqual(ctx.exception.field, "start_raw")
        self.assertEqual(str(ctx.exception), "開始時間は空にできません。")


class TestValidateVideoInputPath(unittest.TestCase):
    def setUp(self):
        self.ws = FormWorkspace()
        self.addCleanup(self.ws.cleanup)

    def test_存在する動画ファイルなら通る(self):
        validate_video_input_path(self.ws.input_file)

    def test_空_存在しない_動画以外の拡張子だとfieldはinput_fileになる(self):
        # Arrange
        txt = self.ws.root / "in.txt"
        txt.write_text("")

        for path in ["", self.ws.missing_input, str(txt)]:
            with self.subTest(path=path):
                # Act
                with self.assertRaises(ValidationError) as ctx:
                    validate_video_input_path(path)

                # Assert
                self.assertEqual(ctx.exception.field, "input_file")


class TestValidateOutputPath(unittest.TestCase):
    def setUp(self):
        self.ws = FormWorkspace()
        self.addCleanup(self.ws.cleanup)

    def test_出力ディレクトリが存在すれば通る(self):
        validate_output_path(self.ws.output())

    def test_空_ディレクトリが無いとfieldはoutput_fileになる(self):
        for path in [" ", self.ws.output_in_missing_dir]:
            with self.subTest(path=path):
                # Act
                with self.assertRaises(ValidationError) as ctx:
                    validate_output_path(path)

                # Assert
                self.assertEqual(ctx.exception.field, "output_file")


if __name__ == "__main__":
    unittest.main()
