import unittest

from shared.errors import ValidationError


class TestValidationError(unittest.TestCase):
    def test_field_defaults_to_none_for_existing_callers(self):
        exc = ValidationError("入力ファイルは空にできません。")
        self.assertIsNone(exc.field)
        self.assertEqual(str(exc), "入力ファイルは空にできません。")

    def test_field_can_be_given(self):
        exc = ValidationError("開始時間は空にできません。", field="start_raw")
        self.assertEqual(exc.field, "start_raw")
        self.assertEqual(str(exc), "開始時間は空にできません。")


if __name__ == "__main__":
    unittest.main()
