import unittest

from shared.errors import ValidationError
from validation.value_validators import (
    parse_time_input,
    validate_crf,
    validate_crop_dimension,
    validate_crop_offset,
    validate_dimension,
    validate_fps,
    validate_gif_width,
    validate_speed_multiplier,
    validate_timestamp_within_duration,
    validate_volume_level,
)


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


class TestValidateFps(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(validate_fps("10", "fps"), 10)

    def test_boundary_low(self):
        self.assertEqual(validate_fps("1", "fps"), 1)

    def test_boundary_high(self):
        self.assertEqual(validate_fps("60", "fps"), 60)

    def test_too_small(self):
        with self.assertRaises(ValidationError):
            validate_fps("0", "fps")

    def test_too_large(self):
        with self.assertRaises(ValidationError):
            validate_fps("61", "fps")

    def test_invalid_text(self):
        with self.assertRaises(ValidationError):
            validate_fps("abc", "fps")


class TestValidateGifWidth(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(validate_gif_width("480", "幅"), 480)

    def test_boundary_low(self):
        self.assertEqual(validate_gif_width("16", "幅"), 16)

    def test_boundary_high(self):
        self.assertEqual(validate_gif_width("1920", "幅"), 1920)

    def test_too_small(self):
        with self.assertRaises(ValidationError):
            validate_gif_width("8", "幅")

    def test_too_large(self):
        with self.assertRaises(ValidationError):
            validate_gif_width("1921", "幅")

    def test_invalid_text(self):
        with self.assertRaises(ValidationError):
            validate_gif_width("abc", "幅")


class TestValidateSpeedMultiplier(unittest.TestCase):
    def test_valid_double(self):
        self.assertAlmostEqual(validate_speed_multiplier("2.0", "速度"), 2.0)

    def test_valid_half(self):
        self.assertAlmostEqual(validate_speed_multiplier("0.5", "速度"), 0.5)

    def test_boundary_low(self):
        self.assertAlmostEqual(validate_speed_multiplier("0.25", "速度"), 0.25)

    def test_boundary_high(self):
        self.assertAlmostEqual(validate_speed_multiplier("4.0", "速度"), 4.0)

    def test_too_small(self):
        with self.assertRaises(ValidationError):
            validate_speed_multiplier("0.1", "速度")

    def test_too_large(self):
        with self.assertRaises(ValidationError):
            validate_speed_multiplier("4.1", "速度")

    def test_invalid_text(self):
        with self.assertRaises(ValidationError):
            validate_speed_multiplier("abc", "速度")

    def test_one_is_valid(self):
        self.assertAlmostEqual(validate_speed_multiplier("1.0", "速度"), 1.0)


class TestValidateTimestampWithinDuration(unittest.TestCase):
    def test_valid_seconds(self):
        self.assertEqual(validate_timestamp_within_duration("10", 30), 10)

    def test_valid_hhmmss(self):
        self.assertEqual(validate_timestamp_within_duration("00:00:10", 30), 10)

    def test_zero_passes(self):
        self.assertEqual(validate_timestamp_within_duration("0", 30), 0)

    def test_exactly_at_duration_raises(self):
        with self.assertRaises(ValidationError):
            validate_timestamp_within_duration("30", 30)

    def test_exceeds_duration_raises(self):
        with self.assertRaises(ValidationError):
            validate_timestamp_within_duration("60", 30)

    def test_invalid_format_raises(self):
        with self.assertRaises(ValidationError):
            validate_timestamp_within_duration("abc", 30)


class TestValidateVolumeLevel(unittest.TestCase):
    def test_valid_float(self):
        self.assertAlmostEqual(validate_volume_level("1.5", "音量"), 1.5)

    def test_valid_integer_string(self):
        self.assertAlmostEqual(validate_volume_level("2", "音量"), 2.0)

    def test_boundary_zero(self):
        self.assertAlmostEqual(validate_volume_level("0.0", "音量"), 0.0)

    def test_boundary_max(self):
        self.assertAlmostEqual(validate_volume_level("10.0", "音量"), 10.0)

    def test_invalid_text(self):
        with self.assertRaises(ValidationError):
            validate_volume_level("abc", "音量")

    def test_too_small(self):
        with self.assertRaises(ValidationError):
            validate_volume_level("-0.1", "音量")

    def test_too_large(self):
        with self.assertRaises(ValidationError):
            validate_volume_level("10.1", "音量")


class TestValidateCropDimension(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(validate_crop_dimension("320", "幅"), 320)

    def test_boundary_min(self):
        self.assertEqual(validate_crop_dimension("2", "幅"), 2)

    def test_boundary_max(self):
        self.assertEqual(validate_crop_dimension("7680", "幅"), 7680)

    def test_too_small(self):
        with self.assertRaises(ValidationError):
            validate_crop_dimension("1", "幅")

    def test_too_large(self):
        with self.assertRaises(ValidationError):
            validate_crop_dimension("7681", "幅")

    def test_non_integer(self):
        with self.assertRaises(ValidationError):
            validate_crop_dimension("abc", "幅")

    def test_float_string(self):
        with self.assertRaises(ValidationError):
            validate_crop_dimension("1.5", "幅")


class TestValidateCropOffset(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(validate_crop_offset("100", "X座標"), 100)

    def test_zero_passes(self):
        self.assertEqual(validate_crop_offset("0", "X座標"), 0)

    def test_negative_raises(self):
        with self.assertRaises(ValidationError):
            validate_crop_offset("-1", "X座標")

    def test_non_integer(self):
        with self.assertRaises(ValidationError):
            validate_crop_offset("abc", "X座標")


class TestValidateCrf(unittest.TestCase):
    def test_valid_range(self):
        self.assertEqual(validate_crf("0", "CRF"), 0)
        self.assertEqual(validate_crf("23", "CRF"), 23)
        self.assertEqual(validate_crf("51", "CRF"), 51)

    def test_too_small(self):
        with self.assertRaises(ValidationError):
            validate_crf("-1", "CRF")

    def test_too_large(self):
        with self.assertRaises(ValidationError):
            validate_crf("52", "CRF")

    def test_non_integer(self):
        with self.assertRaises(ValidationError):
            validate_crf("abc", "CRF")


if __name__ == "__main__":
    unittest.main()
