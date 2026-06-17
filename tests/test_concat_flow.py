import unittest
from unittest.mock import ANY, MagicMock, Mock, patch

from usecases.concat_flow import (
    ConcatForm,
    execute_concat,
    run_concat_iteration,
)
from usecases.flow_result import FlowResult


class TestExecuteConcat(unittest.TestCase):
    @patch("usecases.shared_flow.run_ffmpeg")
    @patch("usecases.concat_flow.choose_concat_strategy")
    @patch("usecases.concat_flow.create_concat_list_file")
    def test_execute_concat_uses_strategy_and_runs_ffmpeg(
        self,
        mock_create_concat_list_file,
        mock_choose_concat_strategy,
        mock_run_ffmpeg,
    ):
        form = ConcatForm(
            count_raw="2",
            input_files=["a.mp4", "b.mp4"],
            output_file="out.mp4",
        )

        mock_create_concat_list_file.return_value.__enter__ = MagicMock(return_value="/tmp/list.txt")
        mock_create_concat_list_file.return_value.__exit__ = MagicMock(return_value=False)

        strategy = MagicMock()
        strategy.build.return_value = ["ffmpeg", "..."]
        mock_choose_concat_strategy.return_value = strategy

        mock_result = MagicMock()
        mock_result.executed = True
        mock_run_ffmpeg.return_value = mock_result

        execute_concat(form, compatible=True)

        mock_create_concat_list_file.assert_called_once_with(["a.mp4", "b.mp4"])
        mock_choose_concat_strategy.assert_called_once_with(True)
        strategy.build.assert_called_once_with("/tmp/list.txt", "out.mp4")
        mock_run_ffmpeg.assert_called_once_with(["ffmpeg", "..."], dry_run=False, progress_callback=ANY)

    @patch("usecases.shared_flow.run_ffmpeg")
    @patch("usecases.concat_flow.choose_concat_strategy")
    @patch("usecases.concat_flow.create_concat_list_file")
    def test_execute_concat_dry_run(
        self,
        mock_create_concat_list_file,
        mock_choose_concat_strategy,
        mock_run_ffmpeg,
    ):
        form = ConcatForm(
            count_raw="2",
            input_files=["a.mp4", "b.mp4"],
            output_file="out.mp4",
        )

        mock_create_concat_list_file.return_value.__enter__ = MagicMock(return_value="/tmp/list.txt")
        mock_create_concat_list_file.return_value.__exit__ = MagicMock(return_value=False)

        strategy = MagicMock()
        strategy.build.return_value = ["ffmpeg", "..."]
        mock_choose_concat_strategy.return_value = strategy

        mock_result = MagicMock()
        mock_result.executed = False
        mock_run_ffmpeg.return_value = mock_result

        execute_concat(form, compatible=True, dry_run=True)

        mock_create_concat_list_file.assert_called_once_with(["a.mp4", "b.mp4"])
        mock_choose_concat_strategy.assert_called_once_with(True)
        strategy.build.assert_called_once_with("/tmp/list.txt", "out.mp4")
        mock_run_ffmpeg.assert_called_once_with(["ffmpeg", "..."], dry_run=True, progress_callback=ANY)

    @patch("usecases.shared_flow.run_ffmpeg")
    @patch("usecases.concat_flow.choose_concat_strategy")
    @patch("usecases.concat_flow.create_concat_list_file")
    def test_execute_concat_removes_temp_file_even_when_ffmpeg_fails(
        self,
        mock_create_concat_list_file,
        mock_choose_concat_strategy,
        mock_run_ffmpeg,
    ):
        from shared.errors import FfmpegExecutionError

        form = ConcatForm(
            count_raw="2",
            input_files=["a.mp4", "b.mp4"],
            output_file="out.mp4",
        )

        mock_create_concat_list_file.return_value.__enter__ = MagicMock(return_value="/tmp/list.txt")
        mock_create_concat_list_file.return_value.__exit__ = MagicMock(return_value=False)

        strategy = MagicMock()
        strategy.build.return_value = ["ffmpeg", "..."]
        mock_choose_concat_strategy.return_value = strategy

        mock_run_ffmpeg.side_effect = FfmpegExecutionError("failed")

        with self.assertRaises(FfmpegExecutionError):
            execute_concat(form, compatible=False)

        mock_create_concat_list_file.return_value.__exit__.assert_called_once()


class TestRunConcatIteration(unittest.TestCase):
    @patch("usecases.concat_flow.collect_concat_input")
    @patch("usecases.concat_flow.build_concat_summary")
    @patch("usecases.shared_flow.handle_generic_review")
    @patch("usecases.concat_flow.execute_concat")
    def test_run_concat_iteration_execute_path(
        self,
        mock_execute_concat,
        mock_handle_concat_review,
        mock_build_concat_summary,
        mock_collect_concat_input,
    ):
        form = ConcatForm()
        updated_form = ConcatForm(
            count_raw="2",
            input_files=["a.mp4", "b.mp4"],
            output_file="out.mp4",
        )
        media_infos = [object(), object()]

        mock_collect_concat_input.return_value = (updated_form, media_infos, True)
        mock_build_concat_summary.return_value = "summary"
        mock_handle_concat_review.return_value = FlowResult(kind="execute", form=updated_form)

        ui = Mock()
        result = run_concat_iteration(form, ui)

        self.assertEqual(result.kind, "done")
        self.assertEqual(result.form, updated_form)
        mock_execute_concat.assert_called_once_with(updated_form, True, dry_run=False)

    @patch("usecases.concat_flow.collect_concat_input")
    @patch("usecases.concat_flow.build_concat_summary")
    @patch("usecases.shared_flow.handle_generic_review")
    @patch("usecases.concat_flow.execute_concat")
    def test_run_concat_iteration_dry_run_path(
        self,
        mock_execute_concat,
        mock_handle_concat_review,
        mock_build_concat_summary,
        mock_collect_concat_input,
    ):
        form = ConcatForm()
        updated_form = ConcatForm(
            count_raw="2",
            input_files=["a.mp4", "b.mp4"],
            output_file="out.mp4",
        )
        media_infos = [object(), object()]

        mock_collect_concat_input.return_value = (updated_form, media_infos, True)
        mock_build_concat_summary.return_value = "summary"
        mock_handle_concat_review.return_value = FlowResult(kind="dry_run", form=updated_form)

        ui = Mock()
        result = run_concat_iteration(form, ui)

        self.assertEqual(result.kind, "done")
        self.assertEqual(result.form, updated_form)
        mock_execute_concat.assert_called_once_with(updated_form, True, dry_run=True)

    @patch("usecases.concat_flow.collect_concat_input")
    @patch("usecases.concat_flow.build_concat_summary")
    @patch("usecases.shared_flow.handle_generic_review")
    @patch("usecases.concat_flow.execute_concat")
    def test_run_concat_iteration_retry_path(
        self,
        mock_execute_concat,
        mock_handle_concat_review,
        mock_build_concat_summary,
        mock_collect_concat_input,
    ):
        form = ConcatForm()
        updated_form = ConcatForm(
            count_raw="2",
            input_files=["a.mp4", "b.mp4"],
            output_file="out.mp4",
        )
        media_infos = [object(), object()]

        mock_collect_concat_input.return_value = (updated_form, media_infos, False)
        mock_build_concat_summary.return_value = "summary"
        mock_handle_concat_review.return_value = FlowResult(kind="retry", form=updated_form)

        ui = Mock()
        result = run_concat_iteration(form, ui)

        self.assertEqual(result.kind, "retry")
        self.assertEqual(result.form, updated_form)
        mock_execute_concat.assert_not_called()

    @patch("usecases.concat_flow.collect_concat_input")
    def test_run_concat_iteration_validation_error_returns_retry(self, mock_collect_concat_input):
        from shared.errors import ValidationError

        form = ConcatForm(
            count_raw="2",
            input_files=["a.mp4", "b.mp4"],
            output_file="out.mp4",
        )
        mock_collect_concat_input.side_effect = ValidationError("bad input")

        ui = Mock()
        result = run_concat_iteration(form, ui)

        self.assertEqual(result.kind, "retry")
        self.assertEqual(result.form, form)


if __name__ == "__main__":
    unittest.main()
