import unittest

from domain.trim_range import TrimRange
from shared.errors import ValidationError


class TestTrimRange(unittest.TestCase):
    def test_create_valid(self):
        value = TrimRange.create(10, 20)
        self.assertEqual(value.start_seconds, 10)
        self.assertEqual(value.end_seconds, 20)
        self.assertEqual(value.duration_seconds, 10)

    def test_create_invalid_order(self):
        with self.assertRaises(ValidationError):
            TrimRange.create(20, 10)

    def test_create_invalid_negative(self):
        with self.assertRaises(ValidationError):
            TrimRange.create(-1, 10)


if __name__ == "__main__":
    unittest.main()
