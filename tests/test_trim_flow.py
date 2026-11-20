import unittest
from dataclasses import replace
from unittest.mock import ANY, Mock, patch

from domain.trim_range import TrimRange
from ffmpeg.commands import build_trim_command
from shared.errors import ValidationError
from tests.form_test_support import FormWorkspace, asked_prompts, make_media_info, make_ui
from usecases.flow_result import FlowResult
from usecases.trim_flow import (
    TrimForm,
    build_trim_command_from_form,
    collect_trim_input,
    execute_trim,
    handle_trim_review,
    run_trim_iteration,
    validate_trim_form,
)


class TestHandleTrimReview(unittest.TestCase):
    def test_handle_trim_review_cancel(self):
        form = TrimForm()
        ui = Mock()
        ui.ask_menu.return_value = "cancel"
        result = handle_trim_review(form, ui)
        self.assertEqual(result.kind, "done")
        self.assertEqual(result.form, form)

    def test_handle_trim_review_restart(self):
        form = TrimForm(input_file="x.mp4", start_raw="10", end_raw="20", output_file="y.mp4")
        ui = Mock()
        ui.ask_menu.return_value = "restart"
        result = handle_trim_review(form, ui)
        self.assertEqual(result.kind, "retry")
        self.assertEqual(result.form, TrimForm())

    def test_handle_trim_review_execute(self):
        form = TrimForm(input_file="x.mp4", start_raw="10", end_raw="20", output_file="y.mp4")
        ui = Mock()
        ui.ask_menu.return_value = "execute"
        result = handle_trim_review(form, ui)
        self.assertEqual(result.kind, "execute")
        self.assertEqual(result.form, form)

    def test_handle_trim_review_dry_run(self):
        form = TrimForm(input_file="x.mp4", start_raw="10", end_raw="20", output_file="y.mp4")
        ui = Mock()
        ui.ask_menu.return_value = "dry_run"
        result = handle_trim_review(form, ui)
        self.assertEqual(result.kind, "dry_run")
        self.assertEqual(result.form, form)

    @patch("usecases.trim_flow.edit_trim_form")
    def test_handle_trim_review_edit(self, mock_edit_form):
        form = TrimForm(input_file="x.mp4", start_raw="10", end_raw="20", output_file="y.mp4")
        edited = TrimForm(input_file="edited.mp4", start_raw="10", end_raw="20", output_file="y.mp4")
        mock_edit_form.return_value = edited
        ui = Mock()
        ui.ask_menu.return_value = "edit"
        result = handle_trim_review(form, ui)
        self.assertEqual(result.kind, "retry")
        self.assertEqual(result.form, edited)
        mock_edit_form.assert_called_once_with(form, ui)


class TestExecuteTrim(unittest.TestCase):
    @patch("usecases.shared_flow.run_ffmpeg")
    @patch("usecases.trim_flow.build_trim_command")
    def test_execute_trim_builds_and_runs_command(self, mock_build_command, mock_run_ffmpeg):
        form = TrimForm(input_file="in.mp4", start_raw="10", end_raw="20", output_file="out.mp4")
        mock_build_command.return_value = ["ffmpeg", "..."]
        execute_trim(form)
        args = mock_build_command.call_args.kwargs
        self.assertEqual(args["input_file"], "in.mp4")
        self.assertEqual(args["output_file"], "out.mp4")
        self.assertEqual(args["trim_range"].start_seconds, 10)
        self.assertEqual(args["trim_range"].end_seconds, 20)
        mock_run_ffmpeg.assert_called_once_with(["ffmpeg", "..."], dry_run=False, progress_callback=ANY)

    @patch("usecases.shared_flow.run_ffmpeg")
    @patch("usecases.trim_flow.build_trim_command")
    def test_execute_trim_dry_run(self, mock_build_command, mock_run_ffmpeg):
        form = TrimForm(input_file="in.mp4", start_raw="10", end_raw="20", output_file="out.mp4")
        mock_build_command.return_value = ["ffmpeg", "..."]
        execute_trim(form, dry_run=True)
        mock_run_ffmpeg.assert_called_once_with(["ffmpeg", "..."], dry_run=True, progress_callback=ANY)


class TestRunTrimIteration(unittest.TestCase):
    @patch("usecases.trim_flow.collect_trim_input")
    @patch("usecases.trim_flow.build_trim_summary")
    @patch("usecases.shared_flow.handle_generic_review")
    @patch("usecases.trim_flow.execute_trim")
    def test_run_trim_iteration_execute_path(
        self, mock_execute_trim, mock_handle_review, mock_build_trim_summary, mock_collect_trim_input
    ):
        form = TrimForm()
        updated_form = TrimForm(input_file="in.mp4", start_raw="10", end_raw="20", output_file="out.mp4")
        media_info = object()
        mock_collect_trim_input.return_value = (updated_form, media_info)
        mock_build_trim_summary.return_value = "summary"
        mock_handle_review.return_value = FlowResult(kind="execute", form=updated_form)
        ui = Mock()
        result = run_trim_iteration(form, ui)
        self.assertEqual(result.kind, "done")
        self.assertEqual(result.form, updated_form)
        mock_execute_trim.assert_called_once_with(updated_form, dry_run=False)

    @patch("usecases.trim_flow.collect_trim_input")
    @patch("usecases.trim_flow.build_trim_summary")
    @patch("usecases.shared_flow.handle_generic_review")
    @patch("usecases.trim_flow.execute_trim")
    def test_run_trim_iteration_dry_run_path(
        self, mock_execute_trim, mock_handle_review, mock_build_trim_summary, mock_collect_trim_input
    ):
        form = TrimForm()
        updated_form = TrimForm(input_file="in.mp4", start_raw="10", end_raw="20", output_file="out.mp4")
        media_info = object()
        mock_collect_trim_input.return_value = (updated_form, media_info)
        mock_build_trim_summary.return_value = "summary"
        mock_handle_review.return_value = FlowResult(kind="dry_run", form=updated_form)
        ui = Mock()
        result = run_trim_iteration(form, ui)
        self.assertEqual(result.kind, "done")
        self.assertEqual(result.form, updated_form)
        mock_execute_trim.assert_called_once_with(updated_form, dry_run=True)

    @patch("usecases.trim_flow.collect_trim_input")
    @patch("usecases.trim_flow.build_trim_summary")
    @patch("usecases.shared_flow.handle_generic_review")
    @patch("usecases.trim_flow.execute_trim")
    def test_run_trim_iteration_retry_path(
        self, mock_execute_trim, mock_handle_review, mock_build_trim_summary, mock_collect_trim_input
    ):
        form = TrimForm()
        updated_form = TrimForm(input_file="in.mp4", start_raw="10", end_raw="20", output_file="out.mp4")
        media_info = object()
        mock_collect_trim_input.return_value = (updated_form, media_info)
        mock_build_trim_summary.return_value = "summary"
        mock_handle_review.return_value = FlowResult(kind="retry", form=updated_form)
        ui = Mock()
        result = run_trim_iteration(form, ui)
        self.assertEqual(result.kind, "retry")
        self.assertEqual(result.form, updated_form)
        mock_execute_trim.assert_not_called()

    @patch("usecases.trim_flow.collect_trim_input")
    def test_run_trim_iteration_validation_error_returns_retry(self, mock_collect_trim_input):
        from shared.errors import ValidationError

        form = TrimForm(input_file="in.mp4", start_raw="10", end_raw="20", output_file="out.mp4")
        mock_collect_trim_input.side_effect = ValidationError("bad input")
        ui = Mock()
        result = run_trim_iteration(form, ui)
        self.assertEqual(result.kind, "retry")
        self.assertEqual(result.form, form)


class TestCollectTrimInput(unittest.TestCase):
    """CLI の質問の順番と、エラーを出すタイミングを固定する。"""

    PROMPTS = [
        "対象の動画ファイルを入力してください",
        "開始時間を入力してください",
        "終了時間を入力してください",
        "出力ファイル名を入力してください",
    ]

    def setUp(self):
        self.ws = FormWorkspace()
        self.addCleanup(self.ws.cleanup)
        patcher = patch("usecases.trim_flow.probe_media_info", return_value=make_media_info(duration_seconds=60.0))
        self.mock_probe = patcher.start()
        self.addCleanup(patcher.stop)

    def test_asks_in_order_and_returns_form_and_media_info(self):
        ui = make_ui([self.ws.input_file, "10", "00:00:20", self.ws.output()])
        form, media_info = collect_trim_input(TrimForm(), ui)
        self.assertEqual(asked_prompts(ui), self.PROMPTS)
        self.assertEqual(form.start_raw, "10")
        self.assertEqual(form.end_raw, "00:00:20")
        self.assertEqual(media_info.duration_seconds, 60.0)

    def test_missing_input_file_fails_before_asking_start(self):
        ui = make_ui([self.ws.missing_input])
        with self.assertRaises(ValidationError):
            collect_trim_input(TrimForm(), ui)
        self.assertEqual(asked_prompts(ui), self.PROMPTS[:1])
        self.mock_probe.assert_not_called()

    def test_empty_start_fails_before_asking_end(self):
        ui = make_ui([self.ws.input_file, " "])
        with self.assertRaises(ValidationError):
            collect_trim_input(TrimForm(), ui)
        self.assertEqual(asked_prompts(ui), self.PROMPTS[:2])

    def test_invalid_start_format_fails_after_asking_end(self):
        ui = make_ui([self.ws.input_file, "abc", "20"])
        with self.assertRaises(ValidationError):
            collect_trim_input(TrimForm(), ui)
        self.assertEqual(asked_prompts(ui), self.PROMPTS[:3])

    def test_end_over_duration_fails_before_asking_output(self):
        ui = make_ui([self.ws.input_file, "10", "61"])
        with self.assertRaises(ValidationError):
            collect_trim_input(TrimForm(), ui)
        self.assertEqual(asked_prompts(ui), self.PROMPTS[:3])

    def test_missing_output_directory_fails_after_asking_output(self):
        ui = make_ui([self.ws.input_file, "10", "20", self.ws.output_in_missing_dir])
        with self.assertRaises(ValidationError):
            collect_trim_input(TrimForm(), ui)
        self.assertEqual(asked_prompts(ui), self.PROMPTS)


class TestValidateTrimForm(unittest.TestCase):
    def setUp(self):
        self.ws = FormWorkspace()
        self.addCleanup(self.ws.cleanup)
        patcher = patch("usecases.trim_flow.probe_media_info", return_value=make_media_info(duration_seconds=60.0))
        self.mock_probe = patcher.start()
        self.addCleanup(patcher.stop)

    def valid_form(self, **overrides) -> TrimForm:
        form = TrimForm(input_file=self.ws.input_file, start_raw="10", end_raw="00:00:20", output_file=self.ws.output())
        return replace(form, **overrides)

    def test_returns_media_info_without_ui(self):
        media_info = validate_trim_form(self.valid_form())
        self.assertEqual(media_info.duration_seconds, 60.0)
        self.mock_probe.assert_called_once_with(self.ws.input_file)

    def test_end_equal_to_duration_is_allowed(self):
        validate_trim_form(self.valid_form(end_raw="60"))

    def test_error_field_is_form_field_name(self):
        cases = [
            ({"input_file": ""}, "input_file"),
            ({"input_file": self.ws.missing_input}, "input_file"),
            ({"input_file": str(self.ws.root / "in.txt")}, "input_file"),
            ({"start_raw": ""}, "start_raw"),
            ({"start_raw": "1:30"}, "start_raw"),
            ({"end_raw": " "}, "end_raw"),
            ({"end_raw": "abc"}, "end_raw"),
            ({"start_raw": "20", "end_raw": "10"}, "start_raw"),
            ({"end_raw": "61"}, "end_raw"),
            ({"output_file": ""}, "output_file"),
            ({"output_file": self.ws.output_in_missing_dir}, "output_file"),
        ]
        (self.ws.root / "in.txt").write_text("")
        for overrides, expected_field in cases:
            with self.subTest(overrides=overrides):
                with self.assertRaises(ValidationError) as ctx:
                    validate_trim_form(self.valid_form(**overrides))
                self.assertEqual(ctx.exception.field, expected_field)

    def test_probe_failure_is_tagged_input_file(self):
        self.mock_probe.side_effect = ValidationError("ffprobe でメディア情報を取得できませんでした")
        with self.assertRaises(ValidationError) as ctx:
            validate_trim_form(self.valid_form())
        self.assertEqual(ctx.exception.field, "input_file")


class TestBuildTrimCommandFromForm(unittest.TestCase):
    def test_matches_build_trim_command(self):
        form = TrimForm(input_file="in.mp4", start_raw="00:00:10", end_raw="20", output_file="out.mp4")
        self.assertEqual(
            build_trim_command_from_form(form),
            build_trim_command(input_file="in.mp4", output_file="out.mp4", trim_range=TrimRange.create(10, 20)),
        )

    def test_invalid_end_raises_with_field(self):
        form = TrimForm(input_file="in.mp4", start_raw="10", end_raw="abc", output_file="out.mp4")
        with self.assertRaises(ValidationError) as ctx:
            build_trim_command_from_form(form)
        self.assertEqual(ctx.exception.field, "end_raw")


if __name__ == "__main__":
    unittest.main()
