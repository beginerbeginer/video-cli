from dataclasses import dataclass, replace

from ffmpeg.commands import build_crop_command
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
from validation.value_validators import require_non_empty, validate_crop_dimension, validate_crop_offset

_FIELD_LABELS: dict[str, str] = {
    "width": "幅",
    "height": "高さ",
    "x": "X座標",
    "y": "Y座標",
    "input_file": "入力ファイル",
    "output_file": "出力ファイル",
}


@dataclass
class CropForm:
    input_file: str = "./input.mp4"
    width: int = 1280
    height: int = 720
    x: int = 0
    y: int = 0
    output_file: str = "./output-cropped.mp4"


def collect_crop_input(form: CropForm, ui: UIPort):
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

    width = validate_crop_dimension(
        ui.ask_text("クロップ幅を入力してください（ピクセル）\n例: 1280", default=str(form.width)), "幅"
    )
    height = validate_crop_dimension(
        ui.ask_text("クロップ高さを入力してください（ピクセル）\n例: 720", default=str(form.height)), "高さ"
    )
    x = validate_crop_offset(
        ui.ask_text("X座標（左端からのオフセット）を入力してください\n例: 0", default=str(form.x)), "X座標"
    )
    y = validate_crop_offset(
        ui.ask_text("Y座標（上端からのオフセット）を入力してください\n例: 0", default=str(form.y)), "Y座標"
    )

    output_file = require_non_empty(
        ui.ask_text("出力ファイル名を入力してください\n例: ./output/cropped.mp4", default=form.output_file),
        "出力ファイル",
    )
    validate_output_directory_exists(output_file)

    return (
        replace(form, input_file=input_file, width=width, height=height, x=x, y=y, output_file=output_file),
        media_info,
    )


def build_crop_summary(form: CropForm, media_info) -> str:
    return "\n".join(
        [
            "実行内容:",
            "- 操作: クロップ",
            f"- 入力: {form.input_file}",
            f"- クロップ範囲: {form.width}x{form.height} (x={form.x}, y={form.y})",
            f"- 出力: {form.output_file}",
        ]
    )


def edit_crop_form(form: CropForm, ui: UIPort) -> CropForm:
    field = ui.ask_menu(
        "修正したい項目を選んでください",
        [
            ("入力ファイル", "input_file"),
            ("幅", "width"),
            ("高さ", "height"),
            ("X座標", "x"),
            ("Y座標", "y"),
            ("出力ファイル", "output_file"),
        ],
    )
    label = _FIELD_LABELS[field]
    if field in ("width", "height"):
        raw = ui.ask_text(f"{label} を再入力してください", default=str(getattr(form, field)))
        value = validate_crop_dimension(raw, label)
    elif field in ("x", "y"):
        raw = ui.ask_text(f"{label} を再入力してください", default=str(getattr(form, field)))
        value = validate_crop_offset(raw, label)
    else:
        value = require_non_empty(
            ui.ask_text(f"{label} を再入力してください", default=getattr(form, field)),
            label,
        )
    return replace(form, **{field: value})


def handle_crop_review(form: CropForm, ui: UIPort) -> FlowResult:
    return handle_generic_review(form, CropForm, lambda f: edit_crop_form(f, ui), ui)


def execute_crop(form: CropForm, dry_run: bool = False) -> None:
    command = build_crop_command(
        input_file=form.input_file,
        output_file=form.output_file,
        width=form.width,
        height=form.height,
        x=form.x,
        y=form.y,
    )

    execute_with_output(command, form.output_file, dry_run)


def run_crop_iteration(form: CropForm, ui: UIPort) -> FlowResult:
    return run_generic_iteration(
        form,
        collect_crop_input,
        build_crop_summary,
        CropForm,
        edit_crop_form,
        execute_crop,
        ui,
    )


def run_crop_flow(ui: UIPort) -> None:
    run_flow(CropForm(), run_crop_iteration, ui)
