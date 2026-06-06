import unittest
from unittest.mock import patch

from usecases.crop_flow import (
    CropForm,
    execute_crop,
    handle_crop_review,
    run_crop_iteration,
)
from usecases.flow_result import FlowResult


class TestHandleCropReview(unittest.TestCase):
    @patch("usecases.shared_flow.ask_review_action", return_value="cancel")
    def test_cancel(self, _mock_action):
        form = CropForm()
        result = handle_crop_review(form)
        self.assertEqual(result.kind, "done")

    @patch("usecases.shared_flow.ask_review_action", return_value="restart")
    def test_restart(self, _mock_action):
        form = CropForm(input_file="in.mp4", width=640, height=360, x=0, y=0, output_file="out.mp4")
        result = handle_crop_review(form)
        self.assertEqual(result.kind, "retry")
        self.assertEqual(result.form, CropForm())

    @patch("usecases.shared_flow.ask_review_action", return_value="execute")
    def test_execute(self, _mock_action):
        form = CropForm(input_file="in.mp4", width=640, height=360, x=0, y=0, output_file="out.mp4")
        result = handle_crop_review(form)
        self.assertEqual(result.kind, "execute")

    @patch("usecases.shared_flow.ask_review_action", return_value="dry_run")
    def test_dry_run(self, _mock_action):
        form = CropForm(input_file="in.mp4", width=640, height=360, x=0, y=0, output_file="out.mp4")
        result = handle_crop_review(form)
        self.assertEqual(result.kind, "dry_run")

    @patch("usecases.shared_flow.ask_review_action", return_value="edit")
    @patch("usecases.crop_flow.edit_crop_form")
    def test_edit(self, mock_edit, _mock_action):
        form = CropForm(input_file="in.mp4", width=640, height=360, x=0, y=0, output_file="out.mp4")
        edited = CropForm(input_file="in.mp4", width=320, height=240, x=0, y=0, output_file="out.mp4")
        mock_edit.return_value = edited
        result = handle_crop_review(form)
        self.assertEqual(result.kind, "retry")
        self.assertEqual(result.form, edited)


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
        result = run_crop_iteration(form)
        self.assertEqual(result.kind, "done")
        mock_execute.assert_called_once_with(updated, dry_run=False)

    @patch("usecases.crop_flow.collect_crop_input")
    def test_validation_error_returns_retry(self, mock_collect):
        from shared.errors import ValidationError

        form = CropForm(input_file="in.mp4", width=640, height=360, x=0, y=0, output_file="out.mp4")
        mock_collect.side_effect = ValidationError("bad")
        result = run_crop_iteration(form)
        self.assertEqual(result.kind, "retry")
        self.assertEqual(result.form, form)


if __name__ == "__main__":
    unittest.main()
