import unittest
from unittest.mock import patch

from usecases.flow_result import FlowResult
from usecases.trim_flow import (
    TrimForm,
    execute_trim,
    handle_trim_review,
    run_trim_iteration,
)


class TestHandleTrimReview(unittest.TestCase):
    @patch("usecases.shared_flow.ask_review_action", return_value="cancel")
    def test_handle_trim_review_cancel(self, _mock_action):
        form = TrimForm()
        result = handle_trim_review(form)

        self.assertEqual(result.kind, "done")
        self.assertEqual(result.form, form)

    @patch("usecases.shared_flow.ask_review_action", return_value="restart")
    def test_handle_trim_review_restart(self, _mock_action):
        form = TrimForm(
            input_file="x.mp4",
            start_raw="10",
            end_raw="20",
            output_file="y.mp4",
        )
        result = handle_trim_review(form)

        self.assertEqual(result.kind, "retry")
        self.assertEqual(result.form, TrimForm())

    @patch("usecases.shared_flow.ask_review_action", return_value="execute")
    def test_handle_trim_review_execute(self, _mock_action):
        form = TrimForm(
            input_file="x.mp4",
            start_raw="10",
            end_raw="20",
            output_file="y.mp4",
        )
        result = handle_trim_review(form)

        self.assertEqual(result.kind, "execute")
        self.assertEqual(result.form, form)

    @patch("usecases.shared_flow.ask_review_action", return_value="dry_run")
    def test_handle_trim_review_dry_run(self, _mock_action):
        form = TrimForm(
            input_file="x.mp4",
            start_raw="10",
            end_raw="20",
            output_file="y.mp4",
        )
        result = handle_trim_review(form)

        self.assertEqual(result.kind, "dry_run")
        self.assertEqual(result.form, form)

    @patch("usecases.shared_flow.ask_review_action", return_value="edit")
    @patch("usecases.trim_flow.edit_trim_form")
    def test_handle_trim_review_edit(self, mock_edit_form, _mock_action):
        form = TrimForm(
            input_file="x.mp4",
            start_raw="10",
            end_raw="20",
            output_file="y.mp4",
        )
        edited = TrimForm(
            input_file="edited.mp4",
            start_raw="10",
            end_raw="20",
            output_file="y.mp4",
        )
        mock_edit_form.return_value = edited

        result = handle_trim_review(form)

        self.assertEqual(result.kind, "retry")
        self.assertEqual(result.form, edited)
        mock_edit_form.assert_called_once_with(form)


class TestExecuteTrim(unittest.TestCase):
    @patch("usecases.trim_flow.run_ffmpeg")
    @patch("usecases.trim_flow.build_trim_command")
    def test_execute_trim_builds_and_runs_command(self, mock_build_command, mock_run_ffmpeg):
        form = TrimForm(
            input_file="in.mp4",
            start_raw="10",
            end_raw="20",
            output_file="out.mp4",
        )
        mock_build_command.return_value = ["ffmpeg", "..."]

        execute_trim(form)

        args = mock_build_command.call_args.kwargs
        self.assertEqual(args["input_file"], "in.mp4")
        self.assertEqual(args["output_file"], "out.mp4")
        self.assertEqual(args["trim_range"].start_seconds, 10)
        self.assertEqual(args["trim_range"].end_seconds, 20)
        mock_run_ffmpeg.assert_called_once_with(["ffmpeg", "..."], dry_run=False)

    @patch("usecases.trim_flow.run_ffmpeg")
    @patch("usecases.trim_flow.build_trim_command")
    def test_execute_trim_dry_run(self, mock_build_command, mock_run_ffmpeg):
        form = TrimForm(
            input_file="in.mp4",
            start_raw="10",
            end_raw="20",
            output_file="out.mp4",
        )
        mock_build_command.return_value = ["ffmpeg", "..."]

        execute_trim(form, dry_run=True)

        args = mock_build_command.call_args.kwargs
        self.assertEqual(args["input_file"], "in.mp4")
        self.assertEqual(args["output_file"], "out.mp4")
        self.assertEqual(args["trim_range"].start_seconds, 10)
        self.assertEqual(args["trim_range"].end_seconds, 20)
        mock_run_ffmpeg.assert_called_once_with(["ffmpeg", "..."], dry_run=True)


class TestRunTrimIteration(unittest.TestCase):
    @patch("usecases.trim_flow.collect_trim_input")
    @patch("usecases.trim_flow.build_trim_summary")
    @patch("usecases.shared_flow.handle_generic_review")
    @patch("usecases.trim_flow.execute_trim")
    def test_run_trim_iteration_execute_path(
        self,
        mock_execute_trim,
        mock_handle_review,
        mock_build_trim_summary,
        mock_collect_trim_input,
    ):
        form = TrimForm()
        updated_form = TrimForm(
            input_file="in.mp4",
            start_raw="10",
            end_raw="20",
            output_file="out.mp4",
        )
        media_info = object()

        mock_collect_trim_input.return_value = (updated_form, media_info)
        mock_build_trim_summary.return_value = "summary"
        mock_handle_review.return_value = FlowResult(kind="execute", form=updated_form)

        result = run_trim_iteration(form)

        self.assertEqual(result.kind, "done")
        self.assertEqual(result.form, updated_form)
        mock_execute_trim.assert_called_once_with(updated_form, dry_run=False)

    @patch("usecases.trim_flow.collect_trim_input")
    @patch("usecases.trim_flow.build_trim_summary")
    @patch("usecases.shared_flow.handle_generic_review")
    @patch("usecases.trim_flow.execute_trim")
    def test_run_trim_iteration_dry_run_path(
        self,
        mock_execute_trim,
        mock_handle_review,
        mock_build_trim_summary,
        mock_collect_trim_input,
    ):
        form = TrimForm()
        updated_form = TrimForm(
            input_file="in.mp4",
            start_raw="10",
            end_raw="20",
            output_file="out.mp4",
        )
        media_info = object()

        mock_collect_trim_input.return_value = (updated_form, media_info)
        mock_build_trim_summary.return_value = "summary"
        mock_handle_review.return_value = FlowResult(kind="dry_run", form=updated_form)

        result = run_trim_iteration(form)

        self.assertEqual(result.kind, "done")
        self.assertEqual(result.form, updated_form)
        mock_execute_trim.assert_called_once_with(updated_form, dry_run=True)

    @patch("usecases.trim_flow.collect_trim_input")
    @patch("usecases.trim_flow.build_trim_summary")
    @patch("usecases.shared_flow.handle_generic_review")
    @patch("usecases.trim_flow.execute_trim")
    def test_run_trim_iteration_retry_path(
        self,
        mock_execute_trim,
        mock_handle_review,
        mock_build_trim_summary,
        mock_collect_trim_input,
    ):
        form = TrimForm()
        updated_form = TrimForm(
            input_file="in.mp4",
            start_raw="10",
            end_raw="20",
            output_file="out.mp4",
        )
        media_info = object()

        mock_collect_trim_input.return_value = (updated_form, media_info)
        mock_build_trim_summary.return_value = "summary"
        mock_handle_review.return_value = FlowResult(kind="retry", form=updated_form)

        result = run_trim_iteration(form)

        self.assertEqual(result.kind, "retry")
        self.assertEqual(result.form, updated_form)
        mock_execute_trim.assert_not_called()

    @patch("usecases.trim_flow.collect_trim_input")
    def test_run_trim_iteration_validation_error_returns_retry(self, mock_collect_trim_input):
        from shared.errors import ValidationError

        form = TrimForm(
            input_file="in.mp4",
            start_raw="10",
            end_raw="20",
            output_file="out.mp4",
        )
        mock_collect_trim_input.side_effect = ValidationError("bad input")

        result = run_trim_iteration(form)

        self.assertEqual(result.kind, "retry")
        self.assertEqual(result.form, form)


if __name__ == "__main__":
    unittest.main()
