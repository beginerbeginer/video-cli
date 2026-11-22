import unittest
from dataclasses import replace
from unittest.mock import ANY, Mock, patch

from ffmpeg.commands import build_fps_command
from shared.errors import ValidationError
from tests.form_test_support import FormWorkspace, asked_prompts, make_media_info, make_ui
from usecases.flow_result import FlowResult
from usecases.fps_flow import (
    FpsForm,
    build_fps_command_from_form,
    collect_fps_input,
    execute_fps,
    run_fps_iteration,
    validate_fps_form,
)


class TestExecuteFps(unittest.TestCase):
    @patch("usecases.shared_flow.run_ffmpeg")
    @patch("usecases.fps_flow.build_fps_command")
    def test_execute_fps_runs_command(self, mock_build, mock_run_ffmpeg):
        form = FpsForm(input_file="in.mp4", fps_raw="30", output_file="out.mp4")
        mock_build.return_value = ["ffmpeg", "..."]
        mock_run_ffmpeg.return_value.executed = True

        execute_fps(form)

        mock_build.assert_called_once_with(
            input_file="in.mp4",
            output_file="out.mp4",
            fps=30.0,
        )
        mock_run_ffmpeg.assert_called_once_with(["ffmpeg", "..."], dry_run=False, progress_callback=ANY)

    @patch("usecases.shared_flow.run_ffmpeg")
    @patch("usecases.fps_flow.build_fps_command")
    def test_execute_fps_dry_run(self, mock_build, mock_run_ffmpeg):
        form = FpsForm(input_file="in.mp4", fps_raw="30", output_file="out.mp4")
        mock_build.return_value = ["ffmpeg", "..."]
        mock_run_ffmpeg.return_value.executed = False

        execute_fps(form, dry_run=True)

        mock_run_ffmpeg.assert_called_once_with(["ffmpeg", "..."], dry_run=True, progress_callback=ANY)


class TestRunFpsIteration(unittest.TestCase):
    @patch("usecases.fps_flow.collect_fps_input")
    @patch("usecases.fps_flow.build_fps_summary")
    @patch("usecases.shared_flow.handle_generic_review")
    @patch("usecases.fps_flow.execute_fps")
    def test_run_fps_iteration_execute_path(self, mock_execute, mock_review, mock_summary, mock_collect):
        form = FpsForm()
        updated = FpsForm(input_file="in.mp4", fps_raw="30", output_file="out.mp4")
        mock_collect.return_value = (updated, object())
        mock_summary.return_value = "summary"
        mock_review.return_value = FlowResult(kind="execute", form=updated)
        ui = Mock()
        result = run_fps_iteration(form, ui)
        self.assertEqual(result.kind, "done")
        mock_execute.assert_called_once_with(updated, dry_run=False)

    @patch("usecases.fps_flow.collect_fps_input")
    @patch("usecases.fps_flow.build_fps_summary")
    @patch("usecases.shared_flow.handle_generic_review")
    @patch("usecases.fps_flow.execute_fps")
    def test_run_fps_iteration_dry_run_path(self, mock_execute, mock_review, mock_summary, mock_collect):
        form = FpsForm()
        updated = FpsForm(input_file="in.mp4", fps_raw="30", output_file="out.mp4")
        mock_collect.return_value = (updated, object())
        mock_summary.return_value = "summary"
        mock_review.return_value = FlowResult(kind="dry_run", form=updated)
        ui = Mock()
        result = run_fps_iteration(form, ui)
        self.assertEqual(result.kind, "done")
        mock_execute.assert_called_once_with(updated, dry_run=True)

    @patch("usecases.fps_flow.collect_fps_input")
    def test_run_fps_iteration_validation_error_returns_retry(self, mock_collect):
        from shared.errors import ValidationError

        form = FpsForm(input_file="in.mp4", fps_raw="30", output_file="out.mp4")
        mock_collect.side_effect = ValidationError("bad input")
        ui = Mock()
        result = run_fps_iteration(form, ui)
        self.assertEqual(result.kind, "retry")
        self.assertEqual(result.form, form)


class TestCollectFpsInput(unittest.TestCase):
    """CLI の質問の順番と、エラーを出すタイミングを固定する。"""

    PROMPTS = [
        "対象の動画ファイルを入力してください",
        "フレームレートを入力してください",
        "出力ファイル名を入力してください",
    ]

    def setUp(self):
        self.ws = FormWorkspace()
        self.addCleanup(self.ws.cleanup)
        patcher = patch("usecases.fps_flow.probe_media_info", return_value=make_media_info())
        self.mock_probe = patcher.start()
        self.addCleanup(patcher.stop)

    def assert_fails_after_asking(self, answers: list[str], asked: int) -> None:
        # Arrange
        ui = make_ui(answers)

        # Act
        with self.assertRaises(ValidationError):
            collect_fps_input(FpsForm(), ui)

        # Assert
        self.assertEqual(asked_prompts(ui), self.PROMPTS[:asked])

    def test_正しく答えると入力_値_出力の順に聞いてFormを返す(self):
        # Arrange
        ui = make_ui([self.ws.input_file, "30", self.ws.output()])

        # Act
        form, media_info = collect_fps_input(FpsForm(), ui)

        # Assert
        self.assertEqual(asked_prompts(ui), self.PROMPTS)
        self.assertEqual(form.fps_raw, "30")
        self.assertEqual(form.output_file, self.ws.output())
        self.assertEqual(media_info, self.mock_probe.return_value)

    def test_入力ファイルが無いと値を聞く前にエラーになる(self):
        self.assert_fails_after_asking([self.ws.missing_input], asked=1)

    def test_値が不正だと出力を聞く前にエラーになる(self):
        self.assert_fails_after_asking([self.ws.input_file, "0"], asked=2)

    def test_出力ディレクトリが無いと出力を聞いたあとでエラーになる(self):
        self.assert_fails_after_asking([self.ws.input_file, "30", self.ws.output_in_missing_dir], asked=3)

    def test_出力の拡張子が対応外だと出力を聞いたあとでエラーになる(self):
        self.assert_fails_after_asking([self.ws.input_file, "30", self.ws.output("out.txt")], asked=3)


class TestValidateFpsForm(unittest.TestCase):
    def setUp(self):
        self.ws = FormWorkspace()
        self.addCleanup(self.ws.cleanup)
        (self.ws.root / "in.txt").write_text("")
        patcher = patch("usecases.fps_flow.probe_media_info", return_value=make_media_info())
        self.mock_probe = patcher.start()
        self.addCleanup(patcher.stop)

    def valid_form(self, **overrides) -> FpsForm:
        form = FpsForm(input_file=self.ws.input_file, fps_raw="30", output_file=self.ws.output())
        return replace(form, **overrides)

    def test_正しいFormを渡すと対話なしでMediaInfoが返る(self):
        # Arrange
        form = self.valid_form()

        # Act
        media_info = validate_fps_form(form)

        # Assert
        self.assertEqual(media_info, self.mock_probe.return_value)
        self.mock_probe.assert_called_once_with(self.ws.input_file)

    def test_項目が不正だとその項目名がfieldに入る(self):
        cases = [
            ({"input_file": ""}, "input_file"),
            ({"input_file": self.ws.missing_input}, "input_file"),
            ({"input_file": str(self.ws.root / "in.txt")}, "input_file"),
            ({"fps_raw": " "}, "fps_raw"),
            ({"fps_raw": "abc"}, "fps_raw"),
            ({"fps_raw": "0"}, "fps_raw"),
            ({"fps_raw": "121"}, "fps_raw"),
            ({"output_file": ""}, "output_file"),
            ({"output_file": self.ws.output_in_missing_dir}, "output_file"),
            ({"output_file": self.ws.output("out.txt")}, "output_file"),
        ]
        for overrides, expected_field in cases:
            with self.subTest(overrides=overrides):
                # Arrange
                form = self.valid_form(**overrides)

                # Act
                with self.assertRaises(ValidationError) as ctx:
                    validate_fps_form(form)

                # Assert
                self.assertEqual(ctx.exception.field, expected_field)

    def test_probeに失敗するとfieldはinput_fileになる(self):
        # Arrange
        self.mock_probe.side_effect = ValidationError("ffprobe でメディア情報を取得できませんでした")

        # Act
        with self.assertRaises(ValidationError) as ctx:
            validate_fps_form(self.valid_form())

        # Assert
        self.assertEqual(ctx.exception.field, "input_file")


class TestBuildFpsCommandFromForm(unittest.TestCase):
    def test_build_fps_commandを直接呼んだときと同じコマンドが返る(self):
        # Arrange
        form = FpsForm(input_file="in.mp4", fps_raw="30", output_file="out.mp4")

        # Act
        command = build_fps_command_from_form(form)

        # Assert
        self.assertEqual(command, build_fps_command(input_file="in.mp4", output_file="out.mp4", fps=30.0))

    def test_値が不正だとその項目名がfieldに入る(self):
        # Arrange
        form = FpsForm(input_file="in.mp4", fps_raw="abc", output_file="out.mp4")

        # Act
        with self.assertRaises(ValidationError) as ctx:
            build_fps_command_from_form(form)

        # Assert
        self.assertEqual(ctx.exception.field, "fps_raw")


if __name__ == "__main__":
    unittest.main()
