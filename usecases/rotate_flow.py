from dataclasses import dataclass, replace

from ffmpeg.commands import ROTATE_FILTERS, build_rotate_command
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
from validation.value_validators import require_non_empty

_DIRECTION_LABELS = [
    ("右に90°回転（スマホ縦動画に多い）", "right90"),
    ("左に90°回転", "left90"),
    ("180°回転", "rot180"),
    ("左右反転（水平）", "hflip"),
    ("上下反転（垂直）", "vflip"),
]

_DIRECTION_DISPLAY = {
    "right90": "右に90°回転",
    "left90": "左に90°回転",
    "rot180": "180°回転",
    "hflip": "左右反転（水平）",
    "vflip": "上下反転（垂直）",
}


@dataclass
class RotateForm:
    input_file: str = "./input.mp4"
    direction: str = "right90"
    output_file: str = "./output-rotated.mp4"


def ask_rotate_direction(default_value: str, ui: UIPort) -> str:
    print(f"回転・反転の方向を選択してください [current: {_DIRECTION_DISPLAY.get(default_value, default_value)}]")
    return ui.ask_menu("", _DIRECTION_LABELS)


def collect_rotate_input(form: RotateForm, ui: UIPort):
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

    direction = ask_rotate_direction(form.direction, ui)
    output_file = require_non_empty(
        ui.ask_text("出力ファイル名を入力してください\n例: ./output/rotated.mp4", default=form.output_file),
        "出力ファイル",
    )
    validate_output_directory_exists(output_file)

    return replace(form, input_file=input_file, direction=direction, output_file=output_file), media_info


def build_rotate_summary(form: RotateForm, media_info) -> str:
    return "\n".join(
        [
            "実行内容:",
            "- 操作: 回転・反転",
            f"- 入力: {form.input_file}",
            f"- 方向: {_DIRECTION_DISPLAY.get(form.direction, form.direction)}（{ROTATE_FILTERS[form.direction]}）",
            f"- 出力: {form.output_file}",
        ]
    )


def edit_rotate_form(form: RotateForm, ui: UIPort) -> RotateForm:
    field = ui.ask_menu(
        "修正したい項目を選んでください",
        [
            ("入力ファイル", "input_file"),
            ("方向", "direction"),
            ("出力ファイル", "output_file"),
        ],
    )
    if field == "direction":
        value = ask_rotate_direction(form.direction, ui)
    else:
        prompts = {
            "input_file": ("入力ファイルを再入力してください", "入力ファイル"),
            "output_file": ("出力ファイルを再入力してください", "出力ファイル"),
        }
        prompt, label = prompts[field]
        value = require_non_empty(ui.ask_text(prompt, default=getattr(form, field)), label)
    return replace(form, **{field: value})


def handle_rotate_review(form: RotateForm, ui: UIPort) -> FlowResult:
    return handle_generic_review(form, RotateForm, lambda f: edit_rotate_form(f, ui), ui)


def execute_rotate(form: RotateForm, dry_run: bool = False) -> None:
    command = build_rotate_command(input_file=form.input_file, output_file=form.output_file, direction=form.direction)

    execute_with_output(command, form.output_file, dry_run)


def run_rotate_iteration(form: RotateForm, ui: UIPort) -> FlowResult:
    return run_generic_iteration(
        form,
        collect_rotate_input,
        build_rotate_summary,
        RotateForm,
        edit_rotate_form,
        execute_rotate,
        ui,
    )


def run_rotate_flow(ui: UIPort) -> None:
    run_flow(RotateForm(), run_rotate_iteration, ui)
