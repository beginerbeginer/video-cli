from dataclasses import dataclass, replace

from domain.trim_range import TrimRange
from ffmpeg.commands import build_trim_command
from ffmpeg.probe import probe_media_info
from shared.formatters import format_media_info_summary, format_seconds_to_hhmmss
from usecases.flow_result import FlowResult
from usecases.shared_flow import execute_with_output, handle_generic_review, run_flow, run_generic_iteration
from usecases.ui_port import UIPort
from validation.file_validators import (
    validate_input_file_exists,
    validate_output_directory_exists,
    validate_video_file_extension,
)
from validation.media_validators import validate_trim_end_within_duration
from validation.value_validators import parse_time_input, require_non_empty


@dataclass
class TrimForm:
    input_file: str = "./input.mp4"
    start_raw: str = ""
    end_raw: str = ""
    output_file: str = "./output-trimmed.mp4"


def build_trim_range(start_raw: str, end_raw: str) -> TrimRange:
    return TrimRange.create(parse_time_input(start_raw), parse_time_input(end_raw))


def collect_trim_input(form: TrimForm, ui: UIPort):
    input_file = require_non_empty(
        ui.ask_text("対象の動画ファイルを入力してください\n例: ./input/video.mp4", default=form.input_file),
        "入力ファイル",
    )
    validate_input_file_exists(input_file)
    validate_video_file_extension(input_file)

    media_info = probe_media_info(input_file)
    print("\n入力動画情報:")
    print(format_media_info_summary(media_info))
    print()

    start_raw = require_non_empty(
        ui.ask_text(
            "開始時間を入力してください\n形式: HH:MM:SS または秒数\n例: 00:01:30 または 90",
            default=form.start_raw or None,
        ),
        "開始時間",
    )
    end_raw = require_non_empty(
        ui.ask_text(
            "終了時間を入力してください\n形式: HH:MM:SS または秒数\n"
            f"終了時間は動画長 {format_seconds_to_hhmmss(media_info.duration_seconds)} 以下を推奨",
            default=form.end_raw or None,
        ),
        "終了時間",
    )

    trim_range = build_trim_range(start_raw, end_raw)
    validate_trim_end_within_duration(trim_range.end_seconds, media_info)

    output_file = require_non_empty(
        ui.ask_text("出力ファイル名を入力してください\n例: ./output/clip.mp4", default=form.output_file),
        "出力ファイル",
    )
    validate_output_directory_exists(output_file)

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
    command = build_trim_command(
        input_file=form.input_file,
        output_file=form.output_file,
        trim_range=build_trim_range(form.start_raw, form.end_raw),
    )

    execute_with_output(command, form.output_file, dry_run)


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
