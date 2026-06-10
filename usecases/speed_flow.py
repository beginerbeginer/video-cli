from dataclasses import dataclass, replace

from ffmpeg.commands import build_speed_command
from ffmpeg.probe import probe_media_info
from shared.formatters import format_media_info_summary
from usecases.flow_result import FlowResult
from usecases.shared_flow import execute_with_output, handle_generic_review, run_flow, run_generic_iteration
from usecases.ui_port import UIPort
from validation.file_validators import (
    validate_input_file_exists,
    validate_output_directory_exists,
    validate_video_file_extension,
)
from validation.value_validators import require_non_empty, validate_speed_multiplier


@dataclass
class SpeedForm:
    input_file: str = "./input.mp4"
    speed_raw: str = "2.0"
    output_file: str = "./output-speed.mp4"


def collect_speed_input(form: SpeedForm, ui: UIPort):
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

    speed_raw = require_non_empty(
        ui.ask_text(
            "速度倍率を入力してください\n数値: 0.25〜4.0（1.0=通常、2.0=2倍速、0.5=スロー）\n例: 2.0",
            default=form.speed_raw,
        ),
        "速度倍率",
    )
    validate_speed_multiplier(speed_raw, "速度倍率")

    output_file = require_non_empty(
        ui.ask_text("出力ファイル名を入力してください\n例: ./output/fast.mp4", default=form.output_file),
        "出力ファイル",
    )
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


def edit_speed_form(form: SpeedForm, ui: UIPort) -> SpeedForm:
    field = ui.ask_menu(
        "修正したい項目を選んでください",
        [
            ("入力ファイル", "input_file"),
            ("速度倍率", "speed_raw"),
            ("出力ファイル", "output_file"),
        ],
    )

    prompts = {
        "input_file": ("入力ファイルを再入力してください", "入力ファイル"),
        "speed_raw": ("速度倍率を再入力してください", "速度倍率"),
        "output_file": ("出力ファイルを再入力してください", "出力ファイル"),
    }
    prompt, label = prompts[field]
    value = require_non_empty(ui.ask_text(prompt, default=getattr(form, field)), label)
    return replace(form, **{field: value})


def handle_speed_review(form: SpeedForm, ui: UIPort) -> FlowResult:
    return handle_generic_review(form, SpeedForm, lambda f: edit_speed_form(f, ui), ui)


def execute_speed(form: SpeedForm, dry_run: bool = False) -> None:
    speed = validate_speed_multiplier(form.speed_raw, "速度倍率")

    command = build_speed_command(
        input_file=form.input_file,
        output_file=form.output_file,
        speed=speed,
    )

    execute_with_output(command, form.output_file, dry_run)


def run_speed_iteration(form: SpeedForm, ui: UIPort) -> FlowResult:
    return run_generic_iteration(
        form,
        collect_speed_input,
        build_speed_summary,
        SpeedForm,
        edit_speed_form,
        execute_speed,
        ui,
    )


def run_speed_flow(ui: UIPort) -> None:
    run_flow(SpeedForm(), run_speed_iteration, ui)
