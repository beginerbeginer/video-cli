import unittest
from dataclasses import replace
from unittest.mock import ANY, Mock, patch

from ffmpeg.commands import build_speed_command
from shared.errors import ValidationError
from tests.form_test_support import FormWorkspace, asked_prompts, make_media_info, make_ui
from usecases.flow_result import FlowResult
from usecases.speed_flow import (
    SpeedForm,
    build_speed_command_from_form,
    collect_speed_input,
    execute_speed,
    handle_speed_review,
    run_speed_iteration,
    validate_speed_form,
)


class TestHandleSpeedReview(unittest.TestCase):
    def test_cancel(self):
        form = SpeedForm()
        ui = Mock()
        ui.ask_menu.return_value = "cancel"
        result = handle_speed_review(form, ui)
        self.assertEqual(result.kind, "done")
        self.assertEqual(result.form, form)

    def test_restart(self):
        form = SpeedForm(input_file="in.mp4", speed_raw="2.0", output_file="out.mp4")
        ui = Mock()
        ui.ask_menu.return_value = "restart"
        result = handle_speed_review(form, ui)
        self.assertEqual(result.kind, "retry")
        self.assertEqual(result.form, SpeedForm())

    def test_execute(self):
        form = SpeedForm(input_file="in.mp4", speed_raw="2.0", output_file="out.mp4")
        ui = Mock()
        ui.ask_menu.return_value = "execute"
        result = handle_speed_review(form, ui)
        self.assertEqual(result.kind, "execute")
        self.assertEqual(result.form, form)

    def test_dry_run(self):
        form = SpeedForm(input_file="in.mp4", speed_raw="2.0", output_file="out.mp4")
        ui = Mock()
        ui.ask_menu.return_value = "dry_run"
        result = handle_speed_review(form, ui)
        self.assertEqual(result.kind, "dry_run")
        self.assertEqual(result.form, form)

    @patch("usecases.speed_flow.edit_speed_form")
    def test_edit(self, mock_edit_form):
        form = SpeedForm(input_file="in.mp4", speed_raw="2.0", output_file="out.mp4")
        edited = SpeedForm(input_file="in.mp4", speed_raw="1.5", output_file="out.mp4")
        mock_edit_form.return_value = edited
        ui = Mock()
        ui.ask_menu.return_value = "edit"
        result = handle_speed_review(form, ui)
        self.assertEqual(result.kind, "retry")
        self.assertEqual(result.form, edited)
        mock_edit_form.assert_called_once_with(form, ui)


class TestExecuteSpeed(unittest.TestCase):
    @patch("usecases.shared_flow.run_ffmpeg")
    @patch("usecases.speed_flow.build_speed_command")
    def test_runs_command(self, mock_build, mock_run_ffmpeg):
        form = SpeedForm(input_file="in.mp4", speed_raw="2.0", output_file="out.mp4")
        mock_build.return_value = ["ffmpeg", "..."]
        execute_speed(form)
        mock_build.assert_called_once_with(input_file="in.mp4", output_file="out.mp4", speed=2.0)
        mock_run_ffmpeg.assert_called_once_with(["ffmpeg", "..."], dry_run=False, progress_callback=ANY)

    @patch("usecases.shared_flow.run_ffmpeg")
    @patch("usecases.speed_flow.build_speed_command")
    def test_dry_run(self, mock_build, mock_run_ffmpeg):
        form = SpeedForm(input_file="in.mp4", speed_raw="2.0", output_file="out.mp4")
        mock_build.return_value = ["ffmpeg", "..."]
        execute_speed(form, dry_run=True)
        mock_run_ffmpeg.assert_called_once_with(["ffmpeg", "..."], dry_run=True, progress_callback=ANY)


class TestRunSpeedIteration(unittest.TestCase):
    @patch("usecases.speed_flow.collect_speed_input")
    @patch("usecases.speed_flow.build_speed_summary")
    @patch("usecases.shared_flow.handle_generic_review")
    @patch("usecases.speed_flow.execute_speed")
    def test_execute_path(self, mock_execute, mock_handle_review, mock_build_summary, mock_collect):
        form = SpeedForm()
        updated_form = SpeedForm(input_file="in.mp4", speed_raw="2.0", output_file="out.mp4")
        media_info = object()
        mock_collect.return_value = (updated_form, media_info)
        mock_build_summary.return_value = "summary"
        mock_handle_review.return_value = FlowResult(kind="execute", form=updated_form)
        ui = Mock()
        result = run_speed_iteration(form, ui)
        self.assertEqual(result.kind, "done")
        mock_execute.assert_called_once_with(updated_form, dry_run=False)

    @patch("usecases.speed_flow.collect_speed_input")
    @patch("usecases.speed_flow.build_speed_summary")
    @patch("usecases.shared_flow.handle_generic_review")
    @patch("usecases.speed_flow.execute_speed")
    def test_dry_run_path(self, mock_execute, mock_handle_review, mock_build_summary, mock_collect):
        form = SpeedForm()
        updated_form = SpeedForm(input_file="in.mp4", speed_raw="2.0", output_file="out.mp4")
        media_info = object()
        mock_collect.return_value = (updated_form, media_info)
        mock_build_summary.return_value = "summary"
        mock_handle_review.return_value = FlowResult(kind="dry_run", form=updated_form)
        ui = Mock()
        result = run_speed_iteration(form, ui)
        self.assertEqual(result.kind, "done")
        mock_execute.assert_called_once_with(updated_form, dry_run=True)

    @patch("usecases.speed_flow.collect_speed_input")
    @patch("usecases.speed_flow.build_speed_summary")
    @patch("usecases.shared_flow.handle_generic_review")
    @patch("usecases.speed_flow.execute_speed")
    def test_retry_path(self, mock_execute, mock_handle_review, mock_build_summary, mock_collect):
        form = SpeedForm()
        updated_form = SpeedForm(input_file="in.mp4", speed_raw="2.0", output_file="out.mp4")
        media_info = object()
        mock_collect.return_value = (updated_form, media_info)
        mock_build_summary.return_value = "summary"
        mock_handle_review.return_value = FlowResult(kind="retry", form=updated_form)
        ui = Mock()
        result = run_speed_iteration(form, ui)
        self.assertEqual(result.kind, "retry")
        mock_execute.assert_not_called()

    @patch("usecases.speed_flow.collect_speed_input")
    def test_validation_error_returns_retry(self, mock_collect):
        from shared.errors import ValidationError

        form = SpeedForm(input_file="in.mp4", speed_raw="2.0", output_file="out.mp4")
        mock_collect.side_effect = ValidationError("bad input")
        ui = Mock()
        result = run_speed_iteration(form, ui)
        self.assertEqual(result.kind, "retry")
        self.assertEqual(result.form, form)


class TestCollectSpeedInput(unittest.TestCase):
    """CLI の質問の順番と、エラーを出すタイミングを固定する。"""

    PROMPTS = [
        "対象の動画ファイルを入力してください",
        "速度倍率を入力してください",
        "出力ファイル名を入力してください",
    ]

    def setUp(self):
        self.ws = FormWorkspace()
        self.addCleanup(self.ws.cleanup)
        patcher = patch("usecases.speed_flow.probe_media_info", return_value=make_media_info())
        self.mock_probe = patcher.start()
        self.addCleanup(patcher.stop)

    def assert_fails_after_asking(self, answers: list[str], asked: int) -> None:
        # Arrange
        ui = make_ui(answers)

        # Act
        with self.assertRaises(ValidationError):
            collect_speed_input(SpeedForm(), ui)

        # Assert
        self.assertEqual(asked_prompts(ui), self.PROMPTS[:asked])

    def test_正しく答えると入力_値_出力の順に聞いてFormを返す(self):
        # Arrange
        ui = make_ui([self.ws.input_file, "2.0", self.ws.output()])

        # Act
        form, media_info = collect_speed_input(SpeedForm(), ui)

        # Assert
        self.assertEqual(asked_prompts(ui), self.PROMPTS)
        self.assertEqual(form.speed_raw, "2.0")
        self.assertEqual(form.output_file, self.ws.output())
        self.assertEqual(media_info, self.mock_probe.return_value)

    def test_入力ファイルが無いと値を聞く前にエラーになる(self):
        self.assert_fails_after_asking([self.ws.missing_input], asked=1)

    def test_値が不正だと出力を聞く前にエラーになる(self):
        self.assert_fails_after_asking([self.ws.input_file, "5"], asked=2)

    def test_出力ディレクトリが無いと出力を聞いたあとでエラーになる(self):
        self.assert_fails_after_asking([self.ws.input_file, "2.0", self.ws.output_in_missing_dir], asked=3)


class TestValidateSpeedForm(unittest.TestCase):
    def setUp(self):
        self.ws = FormWorkspace()
        self.addCleanup(self.ws.cleanup)
        (self.ws.root / "in.txt").write_text("")
        patcher = patch("usecases.speed_flow.probe_media_info", return_value=make_media_info())
        self.mock_probe = patcher.start()
        self.addCleanup(patcher.stop)

    def valid_form(self, **overrides) -> SpeedForm:
        form = SpeedForm(input_file=self.ws.input_file, speed_raw="2.0", output_file=self.ws.output())
        return replace(form, **overrides)

    def test_正しいFormを渡すと対話なしでMediaInfoが返る(self):
        # Arrange
        form = self.valid_form()

        # Act
        media_info = validate_speed_form(form)

        # Assert
        self.assertEqual(media_info, self.mock_probe.return_value)
        self.mock_probe.assert_called_once_with(self.ws.input_file)

    def test_項目が不正だとその項目名がfieldに入る(self):
        cases = [
            ({"input_file": ""}, "input_file"),
            ({"input_file": self.ws.missing_input}, "input_file"),
            ({"input_file": str(self.ws.root / "in.txt")}, "input_file"),
            ({"speed_raw": " "}, "speed_raw"),
            ({"speed_raw": "abc"}, "speed_raw"),
            ({"speed_raw": "0.2"}, "speed_raw"),
            ({"speed_raw": "4.5"}, "speed_raw"),
            ({"speed_raw": "inf"}, "speed_raw"),
            ({"output_file": ""}, "output_file"),
            ({"output_file": self.ws.output_in_missing_dir}, "output_file"),
        ]
        for overrides, expected_field in cases:
            with self.subTest(overrides=overrides):
                # Arrange
                form = self.valid_form(**overrides)

                # Act
                with self.assertRaises(ValidationError) as ctx:
                    validate_speed_form(form)

                # Assert
                self.assertEqual(ctx.exception.field, expected_field)

    def test_probeに失敗するとfieldはinput_fileになる(self):
        # Arrange
        self.mock_probe.side_effect = ValidationError("ffprobe でメディア情報を取得できませんでした")

        # Act
        with self.assertRaises(ValidationError) as ctx:
            validate_speed_form(self.valid_form())

        # Assert
        self.assertEqual(ctx.exception.field, "input_file")


class TestBuildSpeedCommandFromForm(unittest.TestCase):
    def test_build_speed_commandを直接呼んだときと同じコマンドが返る(self):
        # Arrange
        form = SpeedForm(input_file="in.mp4", speed_raw="2.0", output_file="out.mp4")

        # Act
        command = build_speed_command_from_form(form)

        # Assert
        self.assertEqual(command, build_speed_command(input_file="in.mp4", output_file="out.mp4", speed=2.0))

    def test_値が不正だとその項目名がfieldに入る(self):
        # Arrange
        form = SpeedForm(input_file="in.mp4", speed_raw="abc", output_file="out.mp4")

        # Act
        with self.assertRaises(ValidationError) as ctx:
            build_speed_command_from_form(form)

        # Assert
        self.assertEqual(ctx.exception.field, "speed_raw")


if __name__ == "__main__":
    unittest.main()
