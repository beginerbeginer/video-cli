import unittest
from dataclasses import replace
from unittest.mock import ANY, Mock, patch

from ffmpeg.commands import build_volume_command
from shared.errors import ValidationError
from tests.form_test_support import FormWorkspace, asked_prompts, make_media_info, make_ui
from usecases.flow_result import FlowResult
from usecases.volume_flow import (
    VolumeForm,
    build_volume_command_from_form,
    collect_volume_input,
    execute_volume,
    handle_volume_review,
    run_volume_iteration,
    validate_volume_form,
)


class TestHandleVolumeReview(unittest.TestCase):
    def test_handle_volume_review_cancel(self):
        form = VolumeForm()
        ui = Mock()
        ui.ask_menu.return_value = "cancel"
        result = handle_volume_review(form, ui)
        self.assertEqual(result.kind, "done")
        self.assertEqual(result.form, form)

    def test_handle_volume_review_restart(self):
        form = VolumeForm(input_file="in.mp4", volume_raw="2.0", output_file="out.mp4")
        ui = Mock()
        ui.ask_menu.return_value = "restart"
        result = handle_volume_review(form, ui)
        self.assertEqual(result.kind, "retry")
        self.assertEqual(result.form, VolumeForm())

    def test_handle_volume_review_execute(self):
        form = VolumeForm(input_file="in.mp4", volume_raw="2.0", output_file="out.mp4")
        ui = Mock()
        ui.ask_menu.return_value = "execute"
        result = handle_volume_review(form, ui)
        self.assertEqual(result.kind, "execute")
        self.assertEqual(result.form, form)

    def test_handle_volume_review_dry_run(self):
        form = VolumeForm(input_file="in.mp4", volume_raw="2.0", output_file="out.mp4")
        ui = Mock()
        ui.ask_menu.return_value = "dry_run"
        result = handle_volume_review(form, ui)
        self.assertEqual(result.kind, "dry_run")
        self.assertEqual(result.form, form)

    @patch("usecases.volume_flow.edit_volume_form")
    def test_handle_volume_review_edit(self, mock_edit_form):
        form = VolumeForm(input_file="in.mp4", volume_raw="2.0", output_file="out.mp4")
        edited = VolumeForm(input_file="in.mp4", volume_raw="1.5", output_file="out.mp4")
        mock_edit_form.return_value = edited
        ui = Mock()
        ui.ask_menu.return_value = "edit"
        result = handle_volume_review(form, ui)
        self.assertEqual(result.kind, "retry")
        self.assertEqual(result.form, edited)
        mock_edit_form.assert_called_once_with(form, ui)


class TestExecuteVolume(unittest.TestCase):
    @patch("usecases.shared_flow.run_ffmpeg")
    @patch("usecases.volume_flow.build_volume_command")
    def test_execute_volume_runs_command(self, mock_build_volume_command, mock_run_ffmpeg):
        form = VolumeForm(input_file="in.mp4", volume_raw="1.5", output_file="out.mp4")
        mock_build_volume_command.return_value = ["ffmpeg", "..."]
        execute_volume(form)
        mock_build_volume_command.assert_called_once_with(input_file="in.mp4", output_file="out.mp4", volume_level=1.5)
        mock_run_ffmpeg.assert_called_once_with(["ffmpeg", "..."], dry_run=False, progress_callback=ANY)

    @patch("usecases.shared_flow.run_ffmpeg")
    @patch("usecases.volume_flow.build_volume_command")
    def test_execute_volume_dry_run(self, mock_build_volume_command, mock_run_ffmpeg):
        form = VolumeForm(input_file="in.mp4", volume_raw="1.5", output_file="out.mp4")
        mock_build_volume_command.return_value = ["ffmpeg", "..."]
        execute_volume(form, dry_run=True)
        mock_run_ffmpeg.assert_called_once_with(["ffmpeg", "..."], dry_run=True, progress_callback=ANY)


class TestRunVolumeIteration(unittest.TestCase):
    @patch("usecases.volume_flow.collect_volume_input")
    @patch("usecases.volume_flow.build_volume_summary")
    @patch("usecases.shared_flow.handle_generic_review")
    @patch("usecases.volume_flow.execute_volume")
    def test_run_volume_iteration_execute_path(
        self, mock_execute_volume, mock_handle_review, mock_build_volume_summary, mock_collect_volume_input
    ):
        form = VolumeForm()
        updated_form = VolumeForm(input_file="in.mp4", volume_raw="2.0", output_file="out.mp4")
        media_info = object()
        mock_collect_volume_input.return_value = (updated_form, media_info)
        mock_build_volume_summary.return_value = "summary"
        mock_handle_review.return_value = FlowResult(kind="execute", form=updated_form)
        ui = Mock()
        result = run_volume_iteration(form, ui)
        self.assertEqual(result.kind, "done")
        self.assertEqual(result.form, updated_form)
        mock_execute_volume.assert_called_once_with(updated_form, dry_run=False)

    @patch("usecases.volume_flow.collect_volume_input")
    @patch("usecases.volume_flow.build_volume_summary")
    @patch("usecases.shared_flow.handle_generic_review")
    @patch("usecases.volume_flow.execute_volume")
    def test_run_volume_iteration_dry_run_path(
        self, mock_execute_volume, mock_handle_review, mock_build_volume_summary, mock_collect_volume_input
    ):
        form = VolumeForm()
        updated_form = VolumeForm(input_file="in.mp4", volume_raw="2.0", output_file="out.mp4")
        media_info = object()
        mock_collect_volume_input.return_value = (updated_form, media_info)
        mock_build_volume_summary.return_value = "summary"
        mock_handle_review.return_value = FlowResult(kind="dry_run", form=updated_form)
        ui = Mock()
        result = run_volume_iteration(form, ui)
        self.assertEqual(result.kind, "done")
        self.assertEqual(result.form, updated_form)
        mock_execute_volume.assert_called_once_with(updated_form, dry_run=True)

    @patch("usecases.volume_flow.collect_volume_input")
    @patch("usecases.volume_flow.build_volume_summary")
    @patch("usecases.shared_flow.handle_generic_review")
    @patch("usecases.volume_flow.execute_volume")
    def test_run_volume_iteration_retry_path(
        self, mock_execute_volume, mock_handle_review, mock_build_volume_summary, mock_collect_volume_input
    ):
        form = VolumeForm()
        updated_form = VolumeForm(input_file="in.mp4", volume_raw="2.0", output_file="out.mp4")
        media_info = object()
        mock_collect_volume_input.return_value = (updated_form, media_info)
        mock_build_volume_summary.return_value = "summary"
        mock_handle_review.return_value = FlowResult(kind="retry", form=updated_form)
        ui = Mock()
        result = run_volume_iteration(form, ui)
        self.assertEqual(result.kind, "retry")
        self.assertEqual(result.form, updated_form)
        mock_execute_volume.assert_not_called()

    @patch("usecases.volume_flow.collect_volume_input")
    def test_run_volume_iteration_validation_error_returns_retry(self, mock_collect_volume_input):
        from shared.errors import ValidationError

        form = VolumeForm(input_file="in.mp4", volume_raw="2.0", output_file="out.mp4")
        mock_collect_volume_input.side_effect = ValidationError("bad input")
        ui = Mock()
        result = run_volume_iteration(form, ui)
        self.assertEqual(result.kind, "retry")
        self.assertEqual(result.form, form)


class TestCollectVolumeInput(unittest.TestCase):
    """CLI の質問の順番と、エラーを出すタイミングを固定する。"""

    PROMPTS = [
        "対象の動画ファイルを入力してください",
        "音量倍率を入力してください",
        "出力ファイル名を入力してください",
    ]

    def setUp(self):
        self.ws = FormWorkspace()
        self.addCleanup(self.ws.cleanup)
        patcher = patch("usecases.volume_flow.probe_media_info", return_value=make_media_info())
        self.mock_probe = patcher.start()
        self.addCleanup(patcher.stop)

    def assert_fails_after_asking(self, answers: list[str], asked: int) -> None:
        # Arrange
        ui = make_ui(answers)

        # Act
        with self.assertRaises(ValidationError):
            collect_volume_input(VolumeForm(), ui)

        # Assert
        self.assertEqual(asked_prompts(ui), self.PROMPTS[:asked])

    def test_正しく答えると入力_値_出力の順に聞いてFormを返す(self):
        # Arrange
        ui = make_ui([self.ws.input_file, "1.5", self.ws.output()])

        # Act
        form, media_info = collect_volume_input(VolumeForm(), ui)

        # Assert
        self.assertEqual(asked_prompts(ui), self.PROMPTS)
        self.assertEqual(form.volume_raw, "1.5")
        self.assertEqual(form.output_file, self.ws.output())
        self.assertEqual(media_info, self.mock_probe.return_value)

    def test_入力ファイルが無いと値を聞く前にエラーになる(self):
        self.assert_fails_after_asking([self.ws.missing_input], asked=1)

    def test_値が不正だと出力を聞く前にエラーになる(self):
        self.assert_fails_after_asking([self.ws.input_file, "11"], asked=2)

    def test_出力ディレクトリが無いと出力を聞いたあとでエラーになる(self):
        self.assert_fails_after_asking([self.ws.input_file, "1.5", self.ws.output_in_missing_dir], asked=3)


class TestValidateVolumeForm(unittest.TestCase):
    def setUp(self):
        self.ws = FormWorkspace()
        self.addCleanup(self.ws.cleanup)
        (self.ws.root / "in.txt").write_text("")
        patcher = patch("usecases.volume_flow.probe_media_info", return_value=make_media_info())
        self.mock_probe = patcher.start()
        self.addCleanup(patcher.stop)

    def valid_form(self, **overrides) -> VolumeForm:
        form = VolumeForm(input_file=self.ws.input_file, volume_raw="1.5", output_file=self.ws.output())
        return replace(form, **overrides)

    def test_正しいFormを渡すと対話なしでMediaInfoが返る(self):
        # Arrange
        form = self.valid_form()

        # Act
        media_info = validate_volume_form(form)

        # Assert
        self.assertEqual(media_info, self.mock_probe.return_value)
        self.mock_probe.assert_called_once_with(self.ws.input_file)

    def test_項目が不正だとその項目名がfieldに入る(self):
        cases = [
            ({"input_file": ""}, "input_file"),
            ({"input_file": self.ws.missing_input}, "input_file"),
            ({"input_file": str(self.ws.root / "in.txt")}, "input_file"),
            ({"volume_raw": " "}, "volume_raw"),
            ({"volume_raw": "abc"}, "volume_raw"),
            ({"volume_raw": "-0.1"}, "volume_raw"),
            ({"volume_raw": "10.5"}, "volume_raw"),
            ({"volume_raw": "nan"}, "volume_raw"),
            ({"output_file": ""}, "output_file"),
            ({"output_file": self.ws.output_in_missing_dir}, "output_file"),
        ]
        for overrides, expected_field in cases:
            with self.subTest(overrides=overrides):
                # Arrange
                form = self.valid_form(**overrides)

                # Act
                with self.assertRaises(ValidationError) as ctx:
                    validate_volume_form(form)

                # Assert
                self.assertEqual(ctx.exception.field, expected_field)

    def test_probeに失敗するとfieldはinput_fileになる(self):
        # Arrange
        self.mock_probe.side_effect = ValidationError("ffprobe でメディア情報を取得できませんでした")

        # Act
        with self.assertRaises(ValidationError) as ctx:
            validate_volume_form(self.valid_form())

        # Assert
        self.assertEqual(ctx.exception.field, "input_file")


class TestBuildVolumeCommandFromForm(unittest.TestCase):
    def test_build_volume_commandを直接呼んだときと同じコマンドが返る(self):
        # Arrange
        form = VolumeForm(input_file="in.mp4", volume_raw="1.5", output_file="out.mp4")

        # Act
        command = build_volume_command_from_form(form)

        # Assert
        self.assertEqual(command, build_volume_command(input_file="in.mp4", output_file="out.mp4", volume_level=1.5))

    def test_値が不正だとその項目名がfieldに入る(self):
        # Arrange
        form = VolumeForm(input_file="in.mp4", volume_raw="abc", output_file="out.mp4")

        # Act
        with self.assertRaises(ValidationError) as ctx:
            build_volume_command_from_form(form)

        # Assert
        self.assertEqual(ctx.exception.field, "volume_raw")


if __name__ == "__main__":
    unittest.main()
