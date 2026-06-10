from ffmpeg.probe import probe_media_info
from shared.errors import ValidationError
from shared.formatters import format_media_info_summary
from usecases.ui_port import UIPort
from validation.file_validators import validate_input_file_exists, validate_video_file_extension
from validation.value_validators import require_non_empty


def collect_info_input(ui: UIPort):
    raw = ui.ask_text("情報を確認する動画ファイルを入力してください\n例: ./input/video.mp4")
    input_file = require_non_empty(raw, "入力ファイル")
    validate_input_file_exists(input_file)
    validate_video_file_extension(input_file)
    return probe_media_info(input_file)


def run_info_flow(ui: UIPort) -> None:
    try:
        media_info = collect_info_input(ui)
        print("\n動画情報:")
        print(format_media_info_summary(media_info))
        print()
    except ValidationError as exc:
        print(f"\n入力エラー: {exc}")
