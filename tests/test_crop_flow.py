import unittest
from unittest.mock import Mock, patch

from usecases.crop_flow import (
    CropForm,
    edit_crop_form,
    execute_crop,
    handle_crop_review,
    run_crop_iteration,
)
from usecases.flow_result import FlowResult


class TestHandleCropReview(unittest.TestCase):
    def test_cancel(self):
        form = CropForm()
        ui = Mock()
        ui.ask_menu.return_value = "cancel"
        result = handle_crop_review(form, ui)
        self.assertEqual(result.kind, "done")

    def test_restart(self):
        form = CropForm(input_file="in.mp4", width=640, height=360, x=0, y=0, output_file="out.mp4")
        ui = Mock()
        ui.ask_menu.return_value = "restart"
        result = handle_crop_review(form, ui)
        self.assertEqual(result.kind, "retry")
        self.assertEqual(result.form, CropForm())

    def test_execute(self):
        form = CropForm(input_file="in.mp4", width=640, height=360, x=0, y=0, output_file="out.mp4")
        ui = Mock()
        ui.ask_menu.return_value = "execute"
        result = handle_crop_review(form, ui)
        self.assertEqual(result.kind, "execute")

    def test_dry_run(self):
        form = CropForm(input_file="in.mp4", width=640, height=360, x=0, y=0, output_file="out.mp4")
        ui = Mock()
        ui.ask_menu.return_value = "dry_run"
        result = handle_crop_review(form, ui)
        self.assertEqual(result.kind, "dry_run")

    @patch("usecases.crop_flow.edit_crop_form")
    def test_edit(self, mock_edit):
        form = CropForm(input_file="in.mp4", width=640, height=360, x=0, y=0, output_file="out.mp4")
        edited = CropForm(input_file="in.mp4", width=320, height=240, x=0, y=0, output_file="out.mp4")
        mock_edit.return_value = edited
        ui = Mock()
        ui.ask_menu.return_value = "edit"
        result = handle_crop_review(form, ui)
        self.assertEqual(result.kind, "retry")
        self.assertEqual(result.form, edited)
        mock_edit.assert_called_once_with(form, ui)


class TestExecuteCrop(unittest.TestCase):
    @patch("usecases.shared_flow.run_ffmpeg")
    @patch("usecases.crop_flow.build_crop_command")
    def test_runs_command(self, mock_build, mock_run_ffmpeg):
        form = CropForm(input_file="in.mp4", width=640, height=360, x=0, y=0, output_file="out.mp4")
        mock_build.return_value = ["ffmpeg", "..."]
        execute_crop(form)
        mock_build.assert_called_once_with(input_file="in.mp4", output_file="out.mp4", width=640, height=360, x=0, y=0)
        mock_run_ffmpeg.assert_called_once_with(["ffmpeg", "..."], dry_run=False)

    @patch("usecases.shared_flow.run_ffmpeg")
    @patch("usecases.crop_flow.build_crop_command")
    def test_dry_run(self, mock_build, mock_run_ffmpeg):
        form = CropForm(input_file="in.mp4", width=640, height=360, x=0, y=0, output_file="out.mp4")
        mock_build.return_value = ["ffmpeg", "..."]
        execute_crop(form, dry_run=True)
        mock_run_ffmpeg.assert_called_once_with(["ffmpeg", "..."], dry_run=True)


class TestRunCropIteration(unittest.TestCase):
    @patch("usecases.crop_flow.collect_crop_input")
    @patch("usecases.crop_flow.build_crop_summary")
    @patch("usecases.shared_flow.handle_generic_review")
    @patch("usecases.crop_flow.execute_crop")
    def test_execute_path(self, mock_execute, mock_review, mock_summary, mock_collect):
        form = CropForm()
        updated = CropForm(input_file="in.mp4", width=640, height=360, x=0, y=0, output_file="out.mp4")
        mock_collect.return_value = (updated, object())
        mock_summary.return_value = "summary"
        mock_review.return_value = FlowResult(kind="execute", form=updated)
        ui = Mock()
        result = run_crop_iteration(form, ui)
        self.assertEqual(result.kind, "done")
        mock_execute.assert_called_once_with(updated, dry_run=False)

    @patch("usecases.crop_flow.collect_crop_input")
    def test_validation_error_returns_retry(self, mock_collect):
        from shared.errors import ValidationError

        form = CropForm(input_file="in.mp4", width=640, height=360, x=0, y=0, output_file="out.mp4")
        mock_collect.side_effect = ValidationError("bad")
        ui = Mock()
        result = run_crop_iteration(form, ui)
        self.assertEqual(result.kind, "retry")
        self.assertEqual(result.form, form)


class TestEditCropForm(unittest.TestCase):
    def _make_ui(self, field_choice, text_return="100"):
        ui = Mock()
        ui.ask_menu.return_value = field_choice
        ui.ask_text.return_value = text_return
        return ui

    def test_width_prompt_uses_japanese_label(self):
        ui = self._make_ui("width")
        edit_crop_form(CropForm(width=640), ui)
        ui.ask_text.assert_called_once_with("幅 を再入力してください", default="640")

    def test_height_prompt_uses_japanese_label(self):
        ui = self._make_ui("height")
        edit_crop_form(CropForm(height=360), ui)
        ui.ask_text.assert_called_once_with("高さ を再入力してください", default="360")

    def test_x_prompt_uses_japanese_label(self):
        ui = self._make_ui("x")
        edit_crop_form(CropForm(x=0), ui)
        ui.ask_text.assert_called_once_with("X座標 を再入力してください", default="0")

    def test_y_prompt_uses_japanese_label(self):
        ui = self._make_ui("y")
        edit_crop_form(CropForm(y=0), ui)
        ui.ask_text.assert_called_once_with("Y座標 を再入力してください", default="0")


if __name__ == "__main__":
    unittest.main()
