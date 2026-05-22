import unittest
from unittest.mock import patch

from usecases.flow_result import FlowResult
from usecases.thumbnail_flow import (
    ThumbnailForm,
    execute_thumbnail,
    handle_thumbnail_review,
    run_thumbnail_iteration,
)


class TestHandleThumbnailReview(unittest.TestCase):
    @patch("usecases.shared_flow.ask_review_action", return_value="cancel")
    def test_cancel(self, _mock_action):
        form = ThumbnailForm()
        result = handle_thumbnail_review(form)

        self.assertEqual(result.kind, "done")
        self.assertEqual(result.form, form)

    @patch("usecases.shared_flow.ask_review_action", return_value="restart")
    def test_restart(self, _mock_action):
        form = ThumbnailForm(input_file="in.mp4", timestamp_raw="10", output_file="out.jpg")
        result = handle_thumbnail_review(form)

        self.assertEqual(result.kind, "retry")
        self.assertEqual(result.form, ThumbnailForm())

    @patch("usecases.shared_flow.ask_review_action", return_value="execute")
    def test_execute(self, _mock_action):
        form = ThumbnailForm(input_file="in.mp4", timestamp_raw="10", output_file="out.jpg")
        result = handle_thumbnail_review(form)

        self.assertEqual(result.kind, "execute")
        self.assertEqual(result.form, form)

    @patch("usecases.shared_flow.ask_review_action", return_value="dry_run")
    def test_dry_run(self, _mock_action):
        form = ThumbnailForm(input_file="in.mp4", timestamp_raw="10", output_file="out.jpg")
        result = handle_thumbnail_review(form)

        self.assertEqual(result.kind, "dry_run")
        self.assertEqual(result.form, form)

    @patch("usecases.shared_flow.ask_review_action", return_value="edit")
    @patch("usecases.thumbnail_flow.edit_thumbnail_form")
    def test_edit(self, mock_edit_form, _mock_action):
        form = ThumbnailForm(input_file="in.mp4", timestamp_raw="10", output_file="out.jpg")
        edited = ThumbnailForm(input_file="in.mp4", timestamp_raw="20", output_file="out.jpg")
        mock_edit_form.return_value = edited

        result = handle_thumbnail_review(form)

        self.assertEqual(result.kind, "retry")
        self.assertEqual(result.form, edited)
        mock_edit_form.assert_called_once_with(form)


class TestExecuteThumbnail(unittest.TestCase):
    @patch("usecases.thumbnail_flow.run_ffmpeg")
    @patch("usecases.thumbnail_flow.build_thumbnail_command")
    def test_runs_command(self, mock_build, mock_run_ffmpeg):
        form = ThumbnailForm(input_file="in.mp4", timestamp_raw="10", output_file="out.jpg")
        mock_build.return_value = ["ffmpeg", "..."]

        execute_thumbnail(form)

        mock_build.assert_called_once_with(
            input_file="in.mp4",
            output_file="out.jpg",
            timestamp_seconds=10,
        )
        mock_run_ffmpeg.assert_called_once_with(["ffmpeg", "..."], dry_run=False)

    @patch("usecases.thumbnail_flow.run_ffmpeg")
    @patch("usecases.thumbnail_flow.build_thumbnail_command")
    def test_dry_run(self, mock_build, mock_run_ffmpeg):
        form = ThumbnailForm(input_file="in.mp4", timestamp_raw="10", output_file="out.jpg")
        mock_build.return_value = ["ffmpeg", "..."]

        execute_thumbnail(form, dry_run=True)

        mock_run_ffmpeg.assert_called_once_with(["ffmpeg", "..."], dry_run=True)


class TestRunThumbnailIteration(unittest.TestCase):
    @patch("usecases.thumbnail_flow.collect_thumbnail_input")
    @patch("usecases.thumbnail_flow.build_thumbnail_summary")
    @patch("usecases.shared_flow.handle_generic_review")
    @patch("usecases.thumbnail_flow.execute_thumbnail")
    def test_execute_path(
        self,
        mock_execute,
        mock_handle_review,
        mock_build_summary,
        mock_collect,
    ):
        form = ThumbnailForm()
        updated_form = ThumbnailForm(
            input_file="in.mp4", timestamp_raw="10", output_file="out.jpg"
        )
        media_info = object()

        mock_collect.return_value = (updated_form, media_info)
        mock_build_summary.return_value = "summary"
        mock_handle_review.return_value = FlowResult(kind="execute", form=updated_form)

        result = run_thumbnail_iteration(form)

        self.assertEqual(result.kind, "done")
        mock_execute.assert_called_once_with(updated_form, dry_run=False)

    @patch("usecases.thumbnail_flow.collect_thumbnail_input")
    @patch("usecases.thumbnail_flow.build_thumbnail_summary")
    @patch("usecases.shared_flow.handle_generic_review")
    @patch("usecases.thumbnail_flow.execute_thumbnail")
    def test_dry_run_path(
        self,
        mock_execute,
        mock_handle_review,
        mock_build_summary,
        mock_collect,
    ):
        form = ThumbnailForm()
        updated_form = ThumbnailForm(
            input_file="in.mp4", timestamp_raw="10", output_file="out.jpg"
        )
        media_info = object()

        mock_collect.return_value = (updated_form, media_info)
        mock_build_summary.return_value = "summary"
        mock_handle_review.return_value = FlowResult(kind="dry_run", form=updated_form)

        result = run_thumbnail_iteration(form)

        self.assertEqual(result.kind, "done")
        mock_execute.assert_called_once_with(updated_form, dry_run=True)

    @patch("usecases.thumbnail_flow.collect_thumbnail_input")
    @patch("usecases.thumbnail_flow.build_thumbnail_summary")
    @patch("usecases.shared_flow.handle_generic_review")
    @patch("usecases.thumbnail_flow.execute_thumbnail")
    def test_retry_path(
        self,
        mock_execute,
        mock_handle_review,
        mock_build_summary,
        mock_collect,
    ):
        form = ThumbnailForm()
        updated_form = ThumbnailForm(
            input_file="in.mp4", timestamp_raw="10", output_file="out.jpg"
        )
        media_info = object()

        mock_collect.return_value = (updated_form, media_info)
        mock_build_summary.return_value = "summary"
        mock_handle_review.return_value = FlowResult(kind="retry", form=updated_form)

        result = run_thumbnail_iteration(form)

        self.assertEqual(result.kind, "retry")
        mock_execute.assert_not_called()

    @patch("usecases.thumbnail_flow.collect_thumbnail_input")
    def test_validation_error_returns_retry(self, mock_collect):
        from shared.errors import ValidationError

        form = ThumbnailForm(input_file="in.mp4", timestamp_raw="10", output_file="out.jpg")
        mock_collect.side_effect = ValidationError("bad input")

        result = run_thumbnail_iteration(form)

        self.assertEqual(result.kind, "retry")
        self.assertEqual(result.form, form)


if __name__ == "__main__":
    unittest.main()
