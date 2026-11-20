import unittest

from shared.errors import ValidationError


class TestValidationError(unittest.TestCase):
    def test_fieldを省略するとNoneになり今の呼び出しはそのまま動く(self):
        # Act
        exc = ValidationError("入力ファイルは空にできません。")

        # Assert
        self.assertIsNone(exc.field)
        self.assertEqual(str(exc), "入力ファイルは空にできません。")

    def test_fieldを渡すとメッセージと一緒に保持される(self):
        # Act
        exc = ValidationError("開始時間は空にできません。", field="start_raw")

        # Assert
        self.assertEqual(exc.field, "start_raw")
        self.assertEqual(str(exc), "開始時間は空にできません。")


if __name__ == "__main__":
    unittest.main()
