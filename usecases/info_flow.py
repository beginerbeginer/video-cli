from ffmpeg.probe import probe_media_info
from shared.errors import ValidationError
from shared.formatters import format_media_info_summary
from ui.prompts import ask_text, require_non_empty
from validation.file_validators import validate_input_file_exists, validate_video_file_extension


def collect_info_input():
    raw = ask_text("情報を確認する動画ファイルを入力してください\n例: ./input/video.mp4")
    input_file = require_non_empty(raw, "入力ファイル")
    validate_input_file_exists(input_file)
    validate_video_file_extension(input_file)
    return probe_media_info(input_file)


def run_info_flow() -> None:
    try:
        media_info = collect_info_input()
        print("\n動画情報:")
        print(format_media_info_summary(media_info))
        print()
    except ValidationError as exc:
        print(f"\n入力エラー: {exc}")
