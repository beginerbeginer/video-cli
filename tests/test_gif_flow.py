import unittest
from unittest.mock import Mock, patch

from usecases.flow_result import FlowResult
from usecases.gif_flow import (
    GifForm,
    execute_gif,
    handle_gif_review,
    run_gif_iteration,
)


class TestHandleGifReview(unittest.TestCase):
    def test_cancel(self):
        form = GifForm()
        ui = Mock()
        ui.ask_menu.return_value = "cancel"
        result = handle_gif_review(form, ui)
        self.assertEqual(result.kind, "done")
        self.assertEqual(result.form, form)

    def test_restart(self):
        form = GifForm(input_file="in.mp4", fps_raw="10", width_raw="480", output_file="out.gif")
        ui = Mock()
        ui.ask_menu.return_value = "restart"
        result = handle_gif_review(form, ui)
        self.assertEqual(result.kind, "retry")
        self.assertEqual(result.form, GifForm())

    def test_execute(self):
        form = GifForm(input_file="in.mp4", fps_raw="10", width_raw="480", output_file="out.gif")
        ui = Mock()
        ui.ask_menu.return_value = "execute"
        result = handle_gif_review(form, ui)
        self.assertEqual(result.kind, "execute")
        self.assertEqual(result.form, form)

    def test_dry_run(self):
        form = GifForm(input_file="in.mp4", fps_raw="10", width_raw="480", output_file="out.gif")
        ui = Mock()
        ui.ask_menu.return_value = "dry_run"
        result = handle_gif_review(form, ui)
        self.assertEqual(result.kind, "dry_run")
        self.assertEqual(result.form, form)

    @patch("usecases.gif_flow.edit_gif_form")
    def test_edit(self, mock_edit_form):
        form = GifForm(input_file="in.mp4", fps_raw="10", width_raw="480", output_file="out.gif")
        edited = GifForm(input_file="in.mp4", fps_raw="15", width_raw="480", output_file="out.gif")
        mock_edit_form.return_value = edited
        ui = Mock()
        ui.ask_menu.return_value = "edit"
        result = handle_gif_review(form, ui)
        self.assertEqual(result.kind, "retry")
        self.assertEqual(result.form, edited)
        mock_edit_form.assert_called_once_with(form, ui)


class TestExecuteGif(unittest.TestCase):
    @patch("usecases.shared_flow.run_ffmpeg")
    @patch("usecases.gif_flow.build_gif_command")
    def test_runs_command(self, mock_build, mock_run_ffmpeg):
        form = GifForm(input_file="in.mp4", fps_raw="10", width_raw="480", output_file="out.gif")
        mock_build.return_value = ["ffmpeg", "..."]
        execute_gif(form)
        mock_build.assert_called_once_with(input_file="in.mp4", output_file="out.gif", fps=10, width=480)
        mock_run_ffmpeg.assert_called_once_with(["ffmpeg", "..."], dry_run=False)

    @patch("usecases.shared_flow.run_ffmpeg")
    @patch("usecases.gif_flow.build_gif_command")
    def test_dry_run(self, mock_build, mock_run_ffmpeg):
        form = GifForm(input_file="in.mp4", fps_raw="10", width_raw="480", output_file="out.gif")
        mock_build.return_value = ["ffmpeg", "..."]
        execute_gif(form, dry_run=True)
        mock_run_ffmpeg.assert_called_once_with(["ffmpeg", "..."], dry_run=True)


class TestRunGifIteration(unittest.TestCase):
    @patch("usecases.gif_flow.collect_gif_input")
    @patch("usecases.gif_flow.build_gif_summary")
    @patch("usecases.shared_flow.handle_generic_review")
    @patch("usecases.gif_flow.execute_gif")
    def test_execute_path(self, mock_execute, mock_handle_review, mock_build_summary, mock_collect):
        form = GifForm()
        updated_form = GifForm(input_file="in.mp4", fps_raw="10", width_raw="480", output_file="out.gif")
        media_info = object()
        mock_collect.return_value = (updated_form, media_info)
        mock_build_summary.return_value = "summary"
        mock_handle_review.return_value = FlowResult(kind="execute", form=updated_form)
        ui = Mock()
        result = run_gif_iteration(form, ui)
        self.assertEqual(result.kind, "done")
        mock_execute.assert_called_once_with(updated_form, dry_run=False)

    @patch("usecases.gif_flow.collect_gif_input")
    @patch("usecases.gif_flow.build_gif_summary")
    @patch("usecases.shared_flow.handle_generic_review")
    @patch("usecases.gif_flow.execute_gif")
    def test_dry_run_path(self, mock_execute, mock_handle_review, mock_build_summary, mock_collect):
        form = GifForm()
        updated_form = GifForm(input_file="in.mp4", fps_raw="10", width_raw="480", output_file="out.gif")
        media_info = object()
        mock_collect.return_value = (updated_form, media_info)
        mock_build_summary.return_value = "summary"
        mock_handle_review.return_value = FlowResult(kind="dry_run", form=updated_form)
        ui = Mock()
        result = run_gif_iteration(form, ui)
        self.assertEqual(result.kind, "done")
        mock_execute.assert_called_once_with(updated_form, dry_run=True)

    @patch("usecases.gif_flow.collect_gif_input")
    @patch("usecases.gif_flow.build_gif_summary")
    @patch("usecases.shared_flow.handle_generic_review")
    @patch("usecases.gif_flow.execute_gif")
    def test_retry_path(self, mock_execute, mock_handle_review, mock_build_summary, mock_collect):
        form = GifForm()
        updated_form = GifForm(input_file="in.mp4", fps_raw="10", width_raw="480", output_file="out.gif")
        media_info = object()
        mock_collect.return_value = (updated_form, media_info)
        mock_build_summary.return_value = "summary"
        mock_handle_review.return_value = FlowResult(kind="retry", form=updated_form)
        ui = Mock()
        result = run_gif_iteration(form, ui)
        self.assertEqual(result.kind, "retry")
        mock_execute.assert_not_called()

    @patch("usecases.gif_flow.collect_gif_input")
    def test_validation_error_returns_retry(self, mock_collect):
        from shared.errors import ValidationError

        form = GifForm(input_file="in.mp4", fps_raw="10", width_raw="480", output_file="out.gif")
        mock_collect.side_effect = ValidationError("bad input")
        ui = Mock()
        result = run_gif_iteration(form, ui)
        self.assertEqual(result.kind, "retry")
        self.assertEqual(result.form, form)


if __name__ == "__main__":
    unittest.main()
