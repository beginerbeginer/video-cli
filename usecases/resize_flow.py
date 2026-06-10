from dataclasses import dataclass, replace

from ffmpeg.commands import build_resize_command
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
from validation.value_validators import require_non_empty, validate_dimension


@dataclass
class ResizeForm:
    input_file: str = "./input.mp4"
    width_raw: str = "1280"
    height_raw: str = "720"
    output_file: str = "./output-resized.mp4"


def collect_resize_input(form: ResizeForm, ui: UIPort):
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

    width_raw = require_non_empty(
        ui.ask_text("幅を入力してください\n整数: 16〜7680\n例: 1280", default=form.width_raw),
        "幅",
    )
    height_raw = require_non_empty(
        ui.ask_text("高さを入力してください\n整数: 16〜7680\n例: 720", default=form.height_raw),
        "高さ",
    )

    validate_dimension(width_raw, "幅")
    validate_dimension(height_raw, "高さ")

    output_file = require_non_empty(
        ui.ask_text("出力ファイル名を入力してください\n例: ./output/resized.mp4", default=form.output_file),
        "出力ファイル",
    )
    validate_output_directory_exists(output_file)

    return (
        replace(form, input_file=input_file, width_raw=width_raw, height_raw=height_raw, output_file=output_file),
        media_info,
    )


def build_resize_summary(form: ResizeForm, media_info) -> str:
    source_width = media_info.video.width if media_info.video else "?"
    source_height = media_info.video.height if media_info.video else "?"
    return "\n".join(
        [
            "実行内容:",
            "- 操作: 動画サイズ変更",
            f"- 入力: {form.input_file}",
            f"- 元情報: {source_width}x{source_height}",
            f"- 幅: {form.width_raw}",
            f"- 高さ: {form.height_raw}",
            f"- 出力: {form.output_file}",
        ]
    )


def edit_resize_form(form: ResizeForm, ui: UIPort) -> ResizeForm:
    field = ui.ask_menu(
        "修正したい項目を選んでください",
        [
            ("入力ファイル", "input_file"),
            ("幅", "width_raw"),
            ("高さ", "height_raw"),
            ("出力ファイル", "output_file"),
        ],
    )

    prompts = {
        "input_file": ("入力ファイルを再入力してください", "入力ファイル"),
        "width_raw": ("幅を再入力してください", "幅"),
        "height_raw": ("高さを再入力してください", "高さ"),
        "output_file": ("出力ファイルを再入力してください", "出力ファイル"),
    }
    prompt, label = prompts[field]
    value = require_non_empty(ui.ask_text(prompt, default=getattr(form, field)), label)
    return replace(form, **{field: value})


def handle_resize_review(form: ResizeForm, ui: UIPort) -> FlowResult:
    return handle_generic_review(form, ResizeForm, lambda f: edit_resize_form(f, ui), ui)


def execute_resize(form: ResizeForm, dry_run: bool = False) -> None:
    width = validate_dimension(form.width_raw, "幅")
    height = validate_dimension(form.height_raw, "高さ")

    command = build_resize_command(
        input_file=form.input_file,
        output_file=form.output_file,
        width=width,
        height=height,
    )

    execute_with_output(command, form.output_file, dry_run)


def run_resize_iteration(form: ResizeForm, ui: UIPort) -> FlowResult:
    return run_generic_iteration(
        form,
        collect_resize_input,
        build_resize_summary,
        ResizeForm,
        edit_resize_form,
        execute_resize,
        ui,
    )


def run_resize_flow(ui: UIPort) -> None:
    run_flow(ResizeForm(), run_resize_iteration, ui)
