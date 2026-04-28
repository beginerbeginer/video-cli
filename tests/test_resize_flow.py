import unittest
from unittest.mock import patch

from usecases.flow_result import FlowResult
from usecases.resize_flow import (
    ResizeForm,
    execute_resize,
    handle_resize_review,
    run_resize_iteration,
)


class TestHandleResizeReview(unittest.TestCase):
    @patch("usecases.shared_flow.ask_review_action", return_value="cancel")
    def test_handle_resize_review_cancel(self, _mock_action):
        form = ResizeForm()
        result = handle_resize_review(form)

        self.assertEqual(result.kind, "done")
        self.assertEqual(result.form, form)

    @patch("usecases.shared_flow.ask_review_action", return_value="restart")
    def test_handle_resize_review_restart(self, _mock_action):
        form = ResizeForm(
            input_file="in.mp4",
            width_raw="1280",
            height_raw="720",
            output_file="out.mp4",
        )
        result = handle_resize_review(form)

        self.assertEqual(result.kind, "retry")
        self.assertEqual(result.form, ResizeForm())

    @patch("usecases.shared_flow.ask_review_action", return_value="execute")
    def test_handle_resize_review_execute(self, _mock_action):
        form = ResizeForm(
            input_file="in.mp4",
            width_raw="1280",
            height_raw="720",
            output_file="out.mp4",
        )
        result = handle_resize_review(form)

        self.assertEqual(result.kind, "execute")
        self.assertEqual(result.form, form)

    @patch("usecases.shared_flow.ask_review_action", return_value="dry_run")
    def test_handle_resize_review_dry_run(self, _mock_action):
        form = ResizeForm(
            input_file="in.mp4",
            width_raw="1280",
            height_raw="720",
            output_file="out.mp4",
        )
        result = handle_resize_review(form)

        self.assertEqual(result.kind, "dry_run")
        self.assertEqual(result.form, form)

    @patch("usecases.shared_flow.ask_review_action", return_value="edit")
    @patch("usecases.resize_flow.edit_resize_form")
    def test_handle_resize_review_edit(self, mock_edit_form, _mock_action):
        form = ResizeForm(
            input_file="in.mp4",
            width_raw="1280",
            height_raw="720",
            output_file="out.mp4",
        )
        edited = ResizeForm(
            input_file="in.mp4",
            width_raw="640",
            height_raw="720",
            output_file="out.mp4",
        )
        mock_edit_form.return_value = edited

        result = handle_resize_review(form)

        self.assertEqual(result.kind, "retry")
        self.assertEqual(result.form, edited)
        mock_edit_form.assert_called_once_with(form)


class TestExecuteResize(unittest.TestCase):
    @patch("usecases.resize_flow.run_ffmpeg")
    @patch("usecases.resize_flow.build_resize_command")
    def test_execute_resize_runs_command(self, mock_build_resize_command, mock_run_ffmpeg):
        form = ResizeForm(
            input_file="in.mp4",
            width_raw="1280",
            height_raw="720",
            output_file="out.mp4",
        )
        mock_build_resize_command.return_value = ["ffmpeg", "..."]

        execute_resize(form)

        mock_build_resize_command.assert_called_once_with(
            input_file="in.mp4",
            output_file="out.mp4",
            width=1280,
            height=720,
        )
        mock_run_ffmpeg.assert_called_once_with(["ffmpeg", "..."], dry_run=False)

    @patch("usecases.resize_flow.run_ffmpeg")
    @patch("usecases.resize_flow.build_resize_command")
    def test_execute_resize_dry_run(self, mock_build_resize_command, mock_run_ffmpeg):
        form = ResizeForm(
            input_file="in.mp4",
            width_raw="1280",
            height_raw="720",
            output_file="out.mp4",
        )
        mock_build_resize_command.return_value = ["ffmpeg", "..."]

        execute_resize(form, dry_run=True)

        mock_build_resize_command.assert_called_once_with(
            input_file="in.mp4",
            output_file="out.mp4",
            width=1280,
            height=720,
        )
        mock_run_ffmpeg.assert_called_once_with(["ffmpeg", "..."], dry_run=True)


class TestRunResizeIteration(unittest.TestCase):
    @patch("usecases.resize_flow.collect_resize_input")
    @patch("usecases.resize_flow.build_resize_summary")
    @patch("usecases.shared_flow.handle_generic_review")
    @patch("usecases.resize_flow.execute_resize")
    def test_run_resize_iteration_execute_path(
        self,
        mock_execute_resize,
        mock_handle_review,
        mock_build_resize_summary,
        mock_collect_resize_input,
    ):
        form = ResizeForm()
        updated_form = ResizeForm(
            input_file="in.mp4",
            width_raw="1280",
            height_raw="720",
            output_file="out.mp4",
        )
        media_info = object()

        mock_collect_resize_input.return_value = (updated_form, media_info)
        mock_build_resize_summary.return_value = "summary"
        mock_handle_review.return_value = FlowResult(kind="execute", form=updated_form)

        result = run_resize_iteration(form)

        self.assertEqual(result.kind, "done")
        self.assertEqual(result.form, updated_form)
        mock_execute_resize.assert_called_once_with(updated_form, dry_run=False)

    @patch("usecases.resize_flow.collect_resize_input")
    @patch("usecases.resize_flow.build_resize_summary")
    @patch("usecases.shared_flow.handle_generic_review")
    @patch("usecases.resize_flow.execute_resize")
    def test_run_resize_iteration_dry_run_path(
        self,
        mock_execute_resize,
        mock_handle_review,
        mock_build_resize_summary,
        mock_collect_resize_input,
    ):
        form = ResizeForm()
        updated_form = ResizeForm(
            input_file="in.mp4",
            width_raw="1280",
            height_raw="720",
            output_file="out.mp4",
        )
        media_info = object()

        mock_collect_resize_input.return_value = (updated_form, media_info)
        mock_build_resize_summary.return_value = "summary"
        mock_handle_review.return_value = FlowResult(kind="dry_run", form=updated_form)

        result = run_resize_iteration(form)

        self.assertEqual(result.kind, "done")
        self.assertEqual(result.form, updated_form)
        mock_execute_resize.assert_called_once_with(updated_form, dry_run=True)

    @patch("usecases.resize_flow.collect_resize_input")
    @patch("usecases.resize_flow.build_resize_summary")
    @patch("usecases.shared_flow.handle_generic_review")
    @patch("usecases.resize_flow.execute_resize")
    def test_run_resize_iteration_retry_path(
        self,
        mock_execute_resize,
        mock_handle_review,
        mock_build_resize_summary,
        mock_collect_resize_input,
    ):
        form = ResizeForm()
        updated_form = ResizeForm(
            input_file="in.mp4",
            width_raw="1280",
            height_raw="720",
            output_file="out.mp4",
        )
        media_info = object()

        mock_collect_resize_input.return_value = (updated_form, media_info)
        mock_build_resize_summary.return_value = "summary"
        mock_handle_review.return_value = FlowResult(kind="retry", form=updated_form)

        result = run_resize_iteration(form)

        self.assertEqual(result.kind, "retry")
        self.assertEqual(result.form, updated_form)
        mock_execute_resize.assert_not_called()

    @patch("usecases.resize_flow.collect_resize_input")
    def test_run_resize_iteration_validation_error_returns_retry(self, mock_collect_resize_input):
        from shared.errors import ValidationError

        form = ResizeForm(
            input_file="in.mp4",
            width_raw="1280",
            height_raw="720",
            output_file="out.mp4",
        )
        mock_collect_resize_input.side_effect = ValidationError("bad input")

        result = run_resize_iteration(form)

        self.assertEqual(result.kind, "retry")
        self.assertEqual(result.form, form)


if __name__ == "__main__":
    unittest.main()
