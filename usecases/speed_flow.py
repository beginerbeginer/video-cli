from dataclasses import dataclass, replace

from ffmpeg.commands import build_speed_command
from ffmpeg.probe import probe_media_info
from ffmpeg.runner import run_ffmpeg
from shared.command_formatter import format_command
from shared.formatters import format_media_info_summary
from ui.prompts import ask_text, require_non_empty
from ui.review import ask_field_to_edit
from usecases.flow_result import FlowResult
from usecases.shared_flow import handle_generic_review, run_flow, run_generic_iteration
from validation.file_validators import (
    validate_input_file_exists,
    validate_output_directory_exists,
    validate_video_file_extension,
)
from validation.value_validators import validate_speed_multiplier


@dataclass
class SpeedForm:
    input_file: str = "./input.mp4"
    speed_raw: str = "2.0"
    output_file: str = "./output-speed.mp4"


def ask_speed_input_file(default_value: str) -> str:
    return require_non_empty(
        ask_text(
            "対象の動画ファイルを入力してください\n例: ./input/video.mp4",
            default=default_value,
        ),
        "入力ファイル",
    )


def ask_speed_multiplier(default_value: str) -> str:
    return require_non_empty(
        ask_text(
            "速度倍率を入力してください\n数値: 0.25〜4.0（1.0=通常、2.0=2倍速、0.5=スロー）\n例: 2.0",
            default=default_value,
        ),
        "速度倍率",
    )


def ask_speed_output(default_value: str) -> str:
    return require_non_empty(
        ask_text(
            "出力ファイル名を入力してください\n例: ./output/fast.mp4",
            default=default_value,
        ),
        "出力ファイル",
    )


def collect_speed_input(form: SpeedForm):
    input_file = ask_speed_input_file(form.input_file)
    validate_input_file_exists(input_file)
    validate_video_file_extension(input_file)

    media_info = probe_media_info(input_file)
    print("\n入力動画情報:")
    print(format_media_info_summary(media_info))
    print()

    speed_raw = ask_speed_multiplier(form.speed_raw)
    validate_speed_multiplier(speed_raw, "速度倍率")

    output_file = ask_speed_output(form.output_file)
    validate_output_directory_exists(output_file)

    return replace(form, input_file=input_file, speed_raw=speed_raw, output_file=output_file), media_info


def build_speed_summary(form: SpeedForm, media_info) -> str:
    duration = media_info.duration_seconds
    try:
        speed = float(form.speed_raw)
        new_duration = duration / speed
        duration_note = f"{new_duration:.1f}秒"
    except ValueError:
        duration_note = "不明"

    return "\n".join(
        [
            "実行内容:",
            "- 操作: 速度変更",
            f"- 入力: {form.input_file}",
            f"- 元の長さ: {duration:.1f}秒",
            f"- 速度倍率: {form.speed_raw}x",
            f"- 出力の長さ（予測）: {duration_note}",
            f"- 出力: {form.output_file}",
        ]
    )


def edit_speed_form(form: SpeedForm) -> SpeedForm:
    field = ask_field_to_edit(
        [
            ("入力ファイル", "input_file"),
            ("速度倍率", "speed_raw"),
            ("出力ファイル", "output_file"),
        ]
    )

    prompts = {
        "input_file": ("入力ファイルを再入力してください", "入力ファイル"),
        "speed_raw": ("速度倍率を再入力してください", "速度倍率"),
        "output_file": ("出力ファイルを再入力してください", "出力ファイル"),
    }
    prompt, label = prompts[field]
    value = require_non_empty(ask_text(prompt, default=getattr(form, field)), label)
    return replace(form, **{field: value})


def handle_speed_review(form: SpeedForm) -> FlowResult:
    return handle_generic_review(form, SpeedForm, edit_speed_form)


def execute_speed(form: SpeedForm, dry_run: bool = False) -> None:
    speed = validate_speed_multiplier(form.speed_raw, "速度倍率")

    command = build_speed_command(
        input_file=form.input_file,
        output_file=form.output_file,
        speed=speed,
    )

    print("生成された FFmpeg コマンド:")
    print(format_command(command))
    print()

    result = run_ffmpeg(command, dry_run=dry_run)

    if result.executed:
        print(f"完了: {form.output_file}")
    else:
        print("ドライラン完了: 実行はしていません。")


def run_speed_iteration(form: SpeedForm) -> FlowResult:
    return run_generic_iteration(
        form,
        collect_speed_input,
        build_speed_summary,
        SpeedForm,
        edit_speed_form,
        execute_speed,
    )


def run_speed_flow() -> None:
    run_flow(SpeedForm(), run_speed_iteration)
