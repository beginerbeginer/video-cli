from dataclasses import dataclass, replace

from domain.media_info import MediaInfo
from domain.trim_range import TrimRange
from ffmpeg.commands import build_trim_command
from ffmpeg.probe import probe_media_info
from shared.formatters import format_media_info_summary, format_seconds_to_hhmmss
from usecases.flow_result import FlowResult
from usecases.form_validation import form_field, require_field, validate_output_path, validate_video_input_path
from usecases.shared_flow import execute_with_output, handle_generic_review, run_flow, run_generic_iteration
from usecases.ui_port import UIPort
from validation.media_validators import validate_trim_end_within_duration
from validation.value_validators import parse_time_input, require_non_empty


@dataclass
class TrimForm:
    input_file: str = "./input.mp4"
    start_raw: str = ""
    end_raw: str = ""
    output_file: str = "./output-trimmed.mp4"


def validate_trim_input_file(input_file: str) -> MediaInfo:
    validate_video_input_path(input_file)
    with form_field("input_file"):
        return probe_media_info(input_file)


def parse_trim_range(start_raw: str, end_raw: str) -> TrimRange:
    require_field(start_raw, "開始時間", "start_raw")
    require_field(end_raw, "終了時間", "end_raw")
    with form_field("start_raw"):
        start_seconds = parse_time_input(start_raw)
    with form_field("end_raw"):
        end_seconds = parse_time_input(end_raw)
    # 開始 >= 終了 は終了側の誤りとも取れるが、TrimRange のメッセージが「開始時間は…」なので start_raw に付ける
    with form_field("start_raw"):
        return TrimRange.create(start_seconds, end_seconds)


def validate_trim_range_fields(start_raw: str, end_raw: str, media_info: MediaInfo) -> TrimRange:
    trim_range = parse_trim_range(start_raw, end_raw)
    with form_field("end_raw"):
        validate_trim_end_within_duration(trim_range.end_seconds, media_info)
    return trim_range


def validate_trim_output_file(output_file: str) -> None:
    validate_output_path(output_file)


def validate_trim_form(form: TrimForm) -> MediaInfo:
    media_info = validate_trim_input_file(form.input_file)
    validate_trim_range_fields(form.start_raw, form.end_raw, media_info)
    validate_trim_output_file(form.output_file)
    return media_info


def build_trim_command_from_form(form: TrimForm) -> list[str]:
    return build_trim_command(
        input_file=form.input_file,
        output_file=form.output_file,
        trim_range=parse_trim_range(form.start_raw, form.end_raw),
    )


def collect_trim_input(form: TrimForm, ui: UIPort):
    # validate_trim_form を最後にまとめて呼ばないのは、CLI では入力ファイルの誤りを
    # 開始時間などを聞く前に知らせたいため。段階ごとの検証関数を聞いた直後に呼ぶ。
    input_file = ui.ask_text("対象の動画ファイルを入力してください\n例: ./input/video.mp4", default=form.input_file)
    media_info = validate_trim_input_file(input_file)
    print("\n入力動画情報:")
    print(format_media_info_summary(media_info))
    print()

    start_raw = require_field(
        ui.ask_text(
            "開始時間を入力してください\n形式: HH:MM:SS または秒数\n例: 00:01:30 または 90",
            default=form.start_raw or None,
        ),
        "開始時間",
        "start_raw",
    )
    end_raw = require_field(
        ui.ask_text(
            "終了時間を入力してください\n形式: HH:MM:SS または秒数\n"
            f"終了時間は動画長 {format_seconds_to_hhmmss(media_info.duration_seconds)} 以下を推奨",
            default=form.end_raw or None,
        ),
        "終了時間",
        "end_raw",
    )
    validate_trim_range_fields(start_raw, end_raw, media_info)

    output_file = ui.ask_text("出力ファイル名を入力してください\n例: ./output/clip.mp4", default=form.output_file)
    validate_trim_output_file(output_file)

    return (
        replace(form, input_file=input_file, start_raw=start_raw, end_raw=end_raw, output_file=output_file),
        media_info,
    )


def build_trim_summary(form: TrimForm, media_info) -> str:
    return "\n".join(
        [
            "実行内容:",
            "- 操作: 動画の切り出し",
            f"- 入力: {form.input_file}",
            f"- 動画長: {format_seconds_to_hhmmss(media_info.duration_seconds)}",
            f"- 開始: {form.start_raw}",
            f"- 終了: {form.end_raw}",
            f"- 出力: {form.output_file}",
        ]
    )


def edit_trim_form(form: TrimForm, ui: UIPort) -> TrimForm:
    field = ui.ask_menu(
        "修正したい項目を選んでください",
        [
            ("入力ファイル", "input_file"),
            ("開始時間", "start_raw"),
            ("終了時間", "end_raw"),
            ("出力ファイル", "output_file"),
        ],
    )

    updates = {
        "input_file": ("入力ファイルを再入力してください", "入力ファイル"),
        "start_raw": ("開始時間を再入力してください", "開始時間"),
        "end_raw": ("終了時間を再入力してください", "終了時間"),
        "output_file": ("出力ファイルを再入力してください", "出力ファイル"),
    }
    prompt, label = updates[field]
    value = require_non_empty(ui.ask_text(prompt, default=getattr(form, field)), label)
    return replace(form, **{field: value})


def handle_trim_review(form: TrimForm, ui: UIPort) -> FlowResult:
    return handle_generic_review(form, TrimForm, lambda f: edit_trim_form(f, ui), ui)


def execute_trim(form: TrimForm, dry_run: bool = False) -> None:
    execute_with_output(build_trim_command_from_form(form), form.output_file, dry_run)


def run_trim_iteration(form: TrimForm, ui: UIPort) -> FlowResult:
    return run_generic_iteration(
        form,
        collect_trim_input,
        build_trim_summary,
        TrimForm,
        edit_trim_form,
        execute_trim,
        ui,
    )


def run_trim_flow(ui: UIPort) -> None:
    run_flow(TrimForm(), run_trim_iteration, ui)
