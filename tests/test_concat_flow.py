import unittest
from unittest.mock import MagicMock, patch

from usecases.concat_flow import (
    ConcatForm,
    execute_concat,
    execute_reviewed_concat,
    handle_concat_review,
    print_concat_execution_result,
    run_concat_iteration,
    should_return_immediately,
)
from usecases.flow_result import FlowResult


class TestHandleConcatReview(unittest.TestCase):
    @patch("usecases.concat_flow.ask_review_action", return_value="cancel")
    def test_handle_concat_review_cancel(self, _mock_action):
        form = ConcatForm()
        result = handle_concat_review(form)

        self.assertEqual(result.kind, "done")
        self.assertEqual(result.form, form)

    @patch("usecases.concat_flow.ask_review_action", return_value="restart")
    def test_handle_concat_review_restart(self, _mock_action):
        form = ConcatForm(
            count_raw="3",
            input_files=["a.mp4", "b.mp4", "c.mp4"],
            output_file="out.mp4",
        )
        result = handle_concat_review(form)

        self.assertEqual(result.kind, "retry")
        self.assertEqual(result.form, ConcatForm())

    @patch("usecases.concat_flow.ask_review_action", return_value="execute")
    def test_handle_concat_review_execute(self, _mock_action):
        form = ConcatForm(
            count_raw="2",
            input_files=["a.mp4", "b.mp4"],
            output_file="out.mp4",
        )
        result = handle_concat_review(form)

        self.assertEqual(result.kind, "execute")
        self.assertEqual(result.form, form)

    @patch("usecases.concat_flow.ask_review_action", return_value="dry_run")
    def test_handle_concat_review_dry_run(self, _mock_action):
        form = ConcatForm(
            count_raw="2",
            input_files=["a.mp4", "b.mp4"],
            output_file="out.mp4",
        )
        result = handle_concat_review(form)

        self.assertEqual(result.kind, "dry_run")
        self.assertEqual(result.form, form)

    @patch("usecases.concat_flow.ask_review_action", return_value="edit")
    @patch("usecases.concat_flow.edit_concat_form")
    def test_handle_concat_review_edit(self, mock_edit_form, _mock_action):
        form = ConcatForm(
            count_raw="2",
            input_files=["a.mp4", "b.mp4"],
            output_file="out.mp4",
        )
        edited = ConcatForm(
            count_raw="2",
            input_files=["x.mp4", "b.mp4"],
            output_file="out.mp4",
        )
        mock_edit_form.return_value = edited

        result = handle_concat_review(form)

        self.assertEqual(result.kind, "retry")
        self.assertEqual(result.form, edited)
        mock_edit_form.assert_called_once_with(form)


class TestConcatFlowHelpers(unittest.TestCase):
    def test_should_return_immediately_for_retry(self):
        result = FlowResult(kind="retry", form=ConcatForm())
        self.assertTrue(should_return_immediately(result))

    def test_should_return_immediately_for_done(self):
        result = FlowResult(kind="done", form=ConcatForm())
        self.assertTrue(should_return_immediately(result))

    def test_should_not_return_immediately_for_execute(self):
        result = FlowResult(kind="execute", form=ConcatForm())
        self.assertFalse(should_return_immediately(result))

    def test_should_not_return_immediately_for_dry_run(self):
        result = FlowResult(kind="dry_run", form=ConcatForm())
        self.assertFalse(should_return_immediately(result))

    @patch("usecases.concat_flow.execute_concat")
    def test_execute_reviewed_concat_runs_dry_run(self, mock_execute_concat):
        form = ConcatForm(
            count_raw="2",
            input_files=["a.mp4", "b.mp4"],
            output_file="out.mp4",
        )
        review_result = FlowResult(kind="dry_run", form=form)

        result = execute_reviewed_concat(review_result, compatible=True)

        mock_execute_concat.assert_called_once_with(form, True, dry_run=True)
        self.assertEqual(result, FlowResult(kind="done", form=form))

    @patch("usecases.concat_flow.execute_concat")
    def test_execute_reviewed_concat_runs_execute(self, mock_execute_concat):
        form = ConcatForm(
            count_raw="2",
            input_files=["a.mp4", "b.mp4"],
            output_file="out.mp4",
        )
        review_result = FlowResult(kind="execute", form=form)

        result = execute_reviewed_concat(review_result, compatible=False)

        mock_execute_concat.assert_called_once_with(form, False, dry_run=False)
        self.assertEqual(result, FlowResult(kind="done", form=form))

    @patch("builtins.print")
    def test_print_concat_execution_result_for_executed(self, mock_print):
        print_concat_execution_result("out.mp4", executed=True)

        mock_print.assert_called_once_with("完了: out.mp4")

    @patch("builtins.print")
    def test_print_concat_execution_result_for_dry_run(self, mock_print):
        print_concat_execution_result("out.mp4", executed=False)

        mock_print.assert_called_once_with("ドライラン完了: 実行はしていません。")


class TestExecuteConcat(unittest.TestCase):
    @patch("usecases.concat_flow.Path")
    @patch("usecases.concat_flow.run_ffmpeg")
    @patch("usecases.concat_flow.choose_concat_strategy")
    @patch("usecases.concat_flow.create_concat_list_file")
    def test_execute_concat_uses_strategy_and_runs_ffmpeg(
        self,
        mock_create_concat_list_file,
        mock_choose_concat_strategy,
        mock_run_ffmpeg,
        mock_path_cls,
    ):
        form = ConcatForm(
            count_raw="2",
            input_files=["a.mp4", "b.mp4"],
            output_file="out.mp4",
        )

        mock_create_concat_list_file.return_value = "/tmp/list.txt"

        strategy = MagicMock()
        strategy.build.return_value = ["ffmpeg", "..."]
        mock_choose_concat_strategy.return_value = strategy

        mock_result = MagicMock()
        mock_result.executed = True
        mock_run_ffmpeg.return_value = mock_result

        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_path_cls.return_value = mock_path

        execute_concat(form, compatible=True)

        mock_create_concat_list_file.assert_called_once_with(["a.mp4", "b.mp4"])
        mock_choose_concat_strategy.assert_called_once_with(True)
        strategy.build.assert_called_once_with("/tmp/list.txt", "out.mp4")
        mock_run_ffmpeg.assert_called_once_with(["ffmpeg", "..."], dry_run=False)
        mock_path.unlink.assert_called_once()

    @patch("usecases.concat_flow.Path")
    @patch("usecases.concat_flow.run_ffmpeg")
    @patch("usecases.concat_flow.choose_concat_strategy")
    @patch("usecases.concat_flow.create_concat_list_file")
    def test_execute_concat_dry_run(
        self,
        mock_create_concat_list_file,
        mock_choose_concat_strategy,
        mock_run_ffmpeg,
        mock_path_cls,
    ):
        form = ConcatForm(
            count_raw="2",
            input_files=["a.mp4", "b.mp4"],
            output_file="out.mp4",
        )

        mock_create_concat_list_file.return_value = "/tmp/list.txt"

        strategy = MagicMock()
        strategy.build.return_value = ["ffmpeg", "..."]
        mock_choose_concat_strategy.return_value = strategy

        mock_result = MagicMock()
        mock_result.executed = False
        mock_run_ffmpeg.return_value = mock_result

        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_path_cls.return_value = mock_path

        execute_concat(form, compatible=True, dry_run=True)

        mock_create_concat_list_file.assert_called_once_with(["a.mp4", "b.mp4"])
        mock_choose_concat_strategy.assert_called_once_with(True)
        strategy.build.assert_called_once_with("/tmp/list.txt", "out.mp4")
        mock_run_ffmpeg.assert_called_once_with(["ffmpeg", "..."], dry_run=True)
        mock_path.unlink.assert_called_once()

    @patch("usecases.concat_flow.Path")
    @patch("usecases.concat_flow.run_ffmpeg")
    @patch("usecases.concat_flow.choose_concat_strategy")
    @patch("usecases.concat_flow.create_concat_list_file")
    def test_execute_concat_removes_temp_file_even_when_ffmpeg_fails(
        self,
        mock_create_concat_list_file,
        mock_choose_concat_strategy,
        mock_run_ffmpeg,
        mock_path_cls,
    ):
        from shared.errors import FfmpegExecutionError

        form = ConcatForm(
            count_raw="2",
            input_files=["a.mp4", "b.mp4"],
            output_file="out.mp4",
        )

        mock_create_concat_list_file.return_value = "/tmp/list.txt"

        strategy = MagicMock()
        strategy.build.return_value = ["ffmpeg", "..."]
        mock_choose_concat_strategy.return_value = strategy

        mock_run_ffmpeg.side_effect = FfmpegExecutionError("failed")

        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_path_cls.return_value = mock_path

        with self.assertRaises(FfmpegExecutionError):
            execute_concat(form, compatible=False)

        mock_path.unlink.assert_called_once()


class TestRunConcatIteration(unittest.TestCase):
    @patch("usecases.concat_flow.collect_concat_input")
    @patch("usecases.concat_flow.build_concat_summary")
    @patch("usecases.concat_flow.handle_concat_review")
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

        result = run_concat_iteration(form)

        self.assertEqual(result.kind, "done")
        self.assertEqual(result.form, updated_form)
        mock_execute_concat.assert_called_once_with(updated_form, True, dry_run=False)

    @patch("usecases.concat_flow.collect_concat_input")
    @patch("usecases.concat_flow.build_concat_summary")
    @patch("usecases.concat_flow.handle_concat_review")
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

        result = run_concat_iteration(form)

        self.assertEqual(result.kind, "done")
        self.assertEqual(result.form, updated_form)
        mock_execute_concat.assert_called_once_with(updated_form, True, dry_run=True)

    @patch("usecases.concat_flow.collect_concat_input")
    @patch("usecases.concat_flow.build_concat_summary")
    @patch("usecases.concat_flow.handle_concat_review")
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

        result = run_concat_iteration(form)

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

        result = run_concat_iteration(form)

        self.assertEqual(result.kind, "retry")
        self.assertEqual(result.form, form)


if __name__ == "__main__":
    unittest.main()
