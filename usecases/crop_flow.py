from dataclasses import dataclass, replace

from ffmpeg.commands import build_crop_command
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
from validation.value_validators import validate_crop_dimension, validate_crop_offset


@dataclass
class CropForm:
    input_file: str = "./input.mp4"
    width: int = 1280
    height: int = 720
    x: int = 0
    y: int = 0
    output_file: str = "./output-cropped.mp4"


def _ask_int(message: str, default: int, validator, label: str) -> int:
    raw = ask_text(message, default=str(default))
    return validator(raw, label)


def collect_crop_input(form: CropForm):
    input_file = require_non_empty(
        ask_text("対象の動画ファイルを入力してください\n例: ./input/video.mp4", default=form.input_file),
        "入力ファイル",
    )
    validate_input_file_exists(input_file)
    validate_video_file_extension(input_file)

    media_info = probe_media_info(input_file)
    print("\n入力動画情報:")
    print(format_media_info_summary(media_info))
    print()

    width = _ask_int("クロップ幅を入力してください（ピクセル）\n例: 1280", form.width, validate_crop_dimension, "幅")
    height = _ask_int("クロップ高さを入力してください（ピクセル）\n例: 720", form.height, validate_crop_dimension, "高さ")
    x = _ask_int("X座標（左端からのオフセット）を入力してください\n例: 0", form.x, validate_crop_offset, "X座標")
    y = _ask_int("Y座標（上端からのオフセット）を入力してください\n例: 0", form.y, validate_crop_offset, "Y座標")

    output_file = require_non_empty(
        ask_text("出力ファイル名を入力してください\n例: ./output/cropped.mp4", default=form.output_file),
        "出力ファイル",
    )
    validate_output_directory_exists(output_file)

    return replace(form, input_file=input_file, width=width, height=height, x=x, y=y, output_file=output_file), media_info


def build_crop_summary(form: CropForm, media_info) -> str:
    return "\n".join([
        "実行内容:",
        "- 操作: クロップ",
        f"- 入力: {form.input_file}",
        f"- クロップ範囲: {form.width}x{form.height} (x={form.x}, y={form.y})",
        f"- 出力: {form.output_file}",
    ])


def edit_crop_form(form: CropForm) -> CropForm:
    field = ask_field_to_edit([
        ("入力ファイル", "input_file"),
        ("幅", "width"),
        ("高さ", "height"),
        ("X座標", "x"),
        ("Y座標", "y"),
        ("出力ファイル", "output_file"),
    ])
    if field in ("width", "height"):
        raw = ask_text(f"{field} を再入力してください", default=str(getattr(form, field)))
        value = validate_crop_dimension(raw, field)
    elif field in ("x", "y"):
        raw = ask_text(f"{field} を再入力してください", default=str(getattr(form, field)))
        value = validate_crop_offset(raw, field)
    else:
        labels = {"input_file": "入力ファイル", "output_file": "出力ファイル"}
        value = require_non_empty(
            ask_text(f"{labels[field]} を再入力してください", default=getattr(form, field)),
            labels[field],
        )
    return replace(form, **{field: value})


def handle_crop_review(form: CropForm) -> FlowResult:
    return handle_generic_review(form, CropForm, edit_crop_form)


def execute_crop(form: CropForm, dry_run: bool = False) -> None:
    command = build_crop_command(
        input_file=form.input_file,
        output_file=form.output_file,
        width=form.width,
        height=form.height,
        x=form.x,
        y=form.y,
    )

    print("生成された FFmpeg コマンド:")
    print(format_command(command))
    print()

    result = run_ffmpeg(command, dry_run=dry_run)
    if result.executed:
        print(f"完了: {form.output_file}")
    else:
        print("ドライラン完了: 実行はしていません。")


def run_crop_iteration(form: CropForm) -> FlowResult:
    return run_generic_iteration(
        form, collect_crop_input, build_crop_summary, CropForm, edit_crop_form, execute_crop,
    )


def run_crop_flow() -> None:
    run_flow(CropForm(), run_crop_iteration)
