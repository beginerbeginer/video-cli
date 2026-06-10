import unittest
from unittest.mock import MagicMock, Mock, patch

from usecases.info_flow import collect_info_input, run_info_flow


class TestCollectInfoInput(unittest.TestCase):
    @patch("usecases.info_flow.probe_media_info")
    @patch("usecases.info_flow.validate_video_file_extension")
    @patch("usecases.info_flow.validate_input_file_exists")
    def test_returns_media_info(self, mock_exists, mock_ext, mock_probe):
        ui = Mock()
        ui.ask_text.return_value = "in.mp4"
        mock_probe.return_value = MagicMock()

        result = collect_info_input(ui)

        mock_exists.assert_called_once_with("in.mp4")
        mock_ext.assert_called_once_with("in.mp4")
        mock_probe.assert_called_once_with("in.mp4")
        self.assertEqual(result, mock_probe.return_value)

    @patch("usecases.info_flow.validate_input_file_exists")
    def test_empty_input_raises(self, _mock_exists):
        from shared.errors import ValidationError

        ui = Mock()
        ui.ask_text.return_value = ""

        with self.assertRaises(ValidationError):
            collect_info_input(ui)


class TestRunInfoFlow(unittest.TestCase):
    @patch("usecases.info_flow.collect_info_input")
    @patch("usecases.info_flow.format_media_info_summary")
    def test_prints_info(self, mock_format, mock_collect):
        ui = Mock()
        mock_collect.return_value = MagicMock()
        mock_format.return_value = "info text"

        run_info_flow(ui)

        mock_format.assert_called_once_with(mock_collect.return_value)

    @patch("usecases.info_flow.collect_info_input")
    def test_validation_error_is_caught(self, mock_collect):
        from shared.errors import ValidationError

        ui = Mock()
        mock_collect.side_effect = ValidationError("bad")

        run_info_flow(ui)


if __name__ == "__main__":
    unittest.main()
