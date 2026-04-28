from dataclasses import dataclass, replace

from domain.trim_range import TrimRange
from ffmpeg.commands import build_trim_command
from ffmpeg.probe import probe_media_info
from ffmpeg.runner import run_ffmpeg
from shared.command_formatter import format_command
from shared.formatters import format_media_info_summary, format_seconds_to_hhmmss
from ui.prompts import ask_text, require_non_empty
from ui.review import ask_field_to_edit
from usecases.flow_result import FlowResult
from usecases.shared_flow import handle_generic_review, run_flow, run_generic_iteration
from validation.file_validators import (
    validate_input_file_exists,
    validate_output_directory_exists,
    validate_video_file_extension,
)
from validation.media_validators import validate_trim_end_within_duration
from validation.value_validators import parse_time_input

@dataclass
class TrimForm:
    input_file: str = "./input.mp4"
    start_raw: str = ""
    end_raw: str = ""
    output_file: str = "./output-trimmed.mp4"


def ask_trim_input_file(default_value: str) -> str:
    return require_non_empty(
        ask_text(
            "対象の動画ファイルを入力してください\n例: ./input/video.mp4",
            default=default_value,
        ),
        "入力ファイル",
    )


def ask_trim_start(default_value: str | None) -> str:
    return require_non_empty(
        ask_text(
            "開始時間を入力してください\n形式: HH:MM:SS または秒数\n例: 00:01:30 または 90",
            default=default_value,
        ),
        "開始時間",
    )


def ask_trim_end(default_value: str | None, end_limit: str) -> str:
    return require_non_empty(
        ask_text(
            f"終了時間を入力してください\n形式: HH:MM:SS または秒数\n終了時間は動画長 {end_limit} 以下を推奨",
            default=default_value,
        ),
        "終了時間",
    )


def ask_trim_output(default_value: str) -> str:
    return require_non_empty(
        ask_text(
            "出力ファイル名を入力してください\n例: ./output/clip.mp4",
            default=default_value,
        ),
        "出力ファイル",
    )


def build_trim_range(start_raw: str, end_raw: str) -> TrimRange:
    return TrimRange.create(parse_time_input(start_raw), parse_time_input(end_raw))


def collect_trim_input(form: TrimForm):
    input_file = ask_trim_input_file(form.input_file)
    validate_input_file_exists(input_file)
    validate_video_file_extension(input_file)

    media_info = probe_media_info(input_file)
    print("\n入力動画情報:")
    print(format_media_info_summary(media_info))
    print()

    start_raw = ask_trim_start(form.start_raw or None)
    end_raw = ask_trim_end(
        form.end_raw or None,
        format_seconds_to_hhmmss(media_info.duration_seconds),
    )

    trim_range = build_trim_range(start_raw, end_raw)
    validate_trim_end_within_duration(trim_range.end_seconds, media_info)

    output_file = ask_trim_output(form.output_file)
    validate_output_directory_exists(output_file)

    return replace(
        form,
        input_file=input_file,
        start_raw=start_raw,
        end_raw=end_raw,
        output_file=output_file,
    ), media_info


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


def prompt_trim_field_update(prompt: str, value: str, label: str) -> str:
    return require_non_empty(ask_text(prompt, default=value), label)


def edit_trim_form(form: TrimForm) -> TrimForm:
    field = ask_field_to_edit(
        [
            ("入力ファイル", "input_file"),
            ("開始時間", "start_raw"),
            ("終了時間", "end_raw"),
            ("出力ファイル", "output_file"),
        ]
    )

    updates = {
        "input_file": ("入力ファイルを再入力してください", "入力ファイル"),
        "start_raw": ("開始時間を再入力してください", "開始時間"),
        "end_raw": ("終了時間を再入力してください", "終了時間"),
        "output_file": ("出力ファイルを再入力してください", "出力ファイル"),
    }
    prompt, label = updates[field]
    return replace(form, **{field: prompt_trim_field_update(prompt, getattr(form, field), label)})


def handle_trim_review(form: TrimForm) -> FlowResult:
    return handle_generic_review(form, TrimForm, edit_trim_form)


def execute_trim(form: TrimForm, dry_run: bool = False) -> None:
    command = build_trim_command(
        input_file=form.input_file,
        output_file=form.output_file,
        trim_range=build_trim_range(form.start_raw, form.end_raw),
    )

    print("生成された FFmpeg コマンド:")
    print(format_command(command))
    print()

    result = run_ffmpeg(command, dry_run=dry_run)

    if result.executed:
        print(f"完了: {form.output_file}")
    else:
        print("ドライラン完了: 実行はしていません。")


def run_trim_iteration(form: TrimForm) -> FlowResult:
    return run_generic_iteration(
        form,
        collect_trim_input,
        build_trim_summary,
        TrimForm,
        edit_trim_form,
        execute_trim,
    )


def run_trim_flow() -> None:
    run_flow(TrimForm(), run_trim_iteration)
