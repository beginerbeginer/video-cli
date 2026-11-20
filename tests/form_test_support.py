import tempfile
from pathlib import Path
from unittest.mock import Mock

from domain.media_info import AudioStreamInfo, MediaInfo, VideoStreamInfo


def make_media_info(path: str = "in.mp4", duration_seconds: float | None = 60.0) -> MediaInfo:
    return MediaInfo(
        path=path,
        duration_seconds=duration_seconds,
        format_name="mov,mp4,m4a,3gp,3g2,mj2",
        video=VideoStreamInfo(codec_name="h264", width=1920, height=1080, fps=30.0),
        audio=AudioStreamInfo(codec_name="aac"),
    )


class FormWorkspace:
    """フォーム検証のテスト用に、実在する入力ファイルと出力ディレクトリを用意する。

    validator はファイルシステムを見るので、mock せず一時ディレクトリで本物を使う。
    """

    def __init__(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.input_file = str(self.root / "in.mp4")
        Path(self.input_file).write_bytes(b"")
        self.output_dir = self.root / "out"
        self.output_dir.mkdir()

    def output(self, name: str = "out.mp4") -> str:
        return str(self.output_dir / name)

    @property
    def missing_input(self) -> str:
        return str(self.root / "missing.mp4")

    @property
    def output_in_missing_dir(self) -> str:
        return str(self.root / "no-such-dir" / "out.mp4")

    def cleanup(self) -> None:
        self._tmp.cleanup()


def make_ui(answers: list[str]) -> Mock:
    ui = Mock()
    ui.ask_text.side_effect = list(answers)
    return ui


def asked_prompts(ui) -> list[str]:
    """ask_text に渡されたプロンプトの 1 行目を、聞かれた順に返す。"""
    return [call.args[0].splitlines()[0] for call in ui.ask_text.call_args_list]
