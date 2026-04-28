from dataclasses import dataclass, replace

from ffmpeg.commands import build_resize_command
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
from validation.value_validators import validate_dimension

@dataclass
class ResizeForm:
    input_file: str = "./input.mp4"
    width_raw: str = "1280"
    height_raw: str = "720"
    output_file: str = "./output-resized.mp4"


def ask_resize_input_file(default_value: str) -> str:
    return require_non_empty(
        ask_text(
            "対象の動画ファイルを入力してください\n例: ./input/video.mp4",
            default=default_value,
        ),
        "入力ファイル",
    )


def ask_resize_dimension(label: str, default_value: str) -> str:
    return require_non_empty(
        ask_text(
            f"{label}を入力してください\n整数: 16〜7680\n例: {'1280' if label == '幅' else '720'}",
            default=default_value,
        ),
        label,
    )


def ask_resize_output(default_value: str) -> str:
    return require_non_empty(
        ask_text(
            "出力ファイル名を入力してください\n例: ./output/resized.mp4",
            default=default_value,
        ),
        "出力ファイル",
    )


def collect_resize_input(form: ResizeForm):
    input_file = ask_resize_input_file(form.input_file)
    validate_input_file_exists(input_file)
    validate_video_file_extension(input_file)

    media_info = probe_media_info(input_file)
    print("\n入力動画情報:")
    print(format_media_info_summary(media_info))
    print()

    width_raw = ask_resize_dimension("幅", form.width_raw)
    height_raw = ask_resize_dimension("高さ", form.height_raw)

    validate_dimension(width_raw, "幅")
    validate_dimension(height_raw, "高さ")

    output_file = ask_resize_output(form.output_file)
    validate_output_directory_exists(output_file)

    return replace(
        form,
        input_file=input_file,
        width_raw=width_raw,
        height_raw=height_raw,
        output_file=output_file,
    ), media_info


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


def edit_resize_form(form: ResizeForm) -> ResizeForm:
    field = ask_field_to_edit(
        [
            ("入力ファイル", "input_file"),
            ("幅", "width_raw"),
            ("高さ", "height_raw"),
            ("出力ファイル", "output_file"),
        ]
    )

    prompts = {
        "input_file": ("入力ファイルを再入力してください", "入力ファイル"),
        "width_raw": ("幅を再入力してください", "幅"),
        "height_raw": ("高さを再入力してください", "高さ"),
        "output_file": ("出力ファイルを再入力してください", "出力ファイル"),
    }
    prompt, label = prompts[field]
    value = require_non_empty(ask_text(prompt, default=getattr(form, field)), label)
    return replace(form, **{field: value})


def handle_resize_review(form: ResizeForm) -> FlowResult:
    return handle_generic_review(form, ResizeForm, edit_resize_form)


def execute_resize(form: ResizeForm, dry_run: bool = False) -> None:
    width = validate_dimension(form.width_raw, "幅")
    height = validate_dimension(form.height_raw, "高さ")

    command = build_resize_command(
        input_file=form.input_file,
        output_file=form.output_file,
        width=width,
        height=height,
    )

    print("生成された FFmpeg コマンド:")
    print(format_command(command))
    print()

    result = run_ffmpeg(command, dry_run=dry_run)

    if result.executed:
        print(f"完了: {form.output_file}")
    else:
        print("ドライラン完了: 実行はしていません。")


def run_resize_iteration(form: ResizeForm) -> FlowResult:
    return run_generic_iteration(
        form,
        collect_resize_input,
        build_resize_summary,
        ResizeForm,
        edit_resize_form,
        execute_resize,
    )


def run_resize_flow() -> None:
    run_flow(ResizeForm(), run_resize_iteration)
