import unittest

from shared.errors import ValidationError
from validation.value_validators import parse_time_input, validate_dimension


class TestParseTimeInput(unittest.TestCase):
    def test_seconds(self):
        self.assertEqual(parse_time_input("90"), 90)

    def test_hhmmss(self):
        self.assertEqual(parse_time_input("00:01:30"), 90)

    def test_hhmmss_hours(self):
        self.assertEqual(parse_time_input("01:00:00"), 3600)

    def test_invalid_format(self):
        with self.assertRaises(ValidationError):
            parse_time_input("1:30")

    def test_zero(self):
        self.assertEqual(parse_time_input("0"), 0)


class TestValidateDimension(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(validate_dimension("1280", "幅"), 1280)

    def test_invalid_text(self):
        with self.assertRaises(ValidationError):
            validate_dimension("abc", "幅")

    def test_too_small(self):
        with self.assertRaises(ValidationError):
            validate_dimension("8", "幅")

    def test_too_large(self):
        with self.assertRaises(ValidationError):
            validate_dimension("9999", "幅")

    def test_boundary_low(self):
        self.assertEqual(validate_dimension("16", "幅"), 16)

    def test_boundary_high(self):
        self.assertEqual(validate_dimension("7680", "幅"), 7680)


if __name__ == "__main__":
    unittest.main()
