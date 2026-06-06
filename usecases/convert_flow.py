from dataclasses import dataclass, replace

from ffmpeg.commands import build_convert_command
from ffmpeg.probe import probe_media_info
from shared.formatters import format_media_info_summary
from ui.prompts import ask_text, require_non_empty
from ui.review import ask_field_to_edit
from usecases.flow_result import FlowResult
from usecases.shared_flow import execute_with_output, handle_generic_review, run_flow, run_generic_iteration
from validation.file_validators import (
    validate_different_extension,
    validate_input_file_exists,
    validate_output_directory_exists,
    validate_video_file_extension,
)


@dataclass
class ConvertForm:
    input_file: str = "./input.mov"
    output_file: str = "./output.mp4"


def ask_convert_input_file(default_value: str) -> str:
    return require_non_empty(
        ask_text("対象の動画ファイルを入力してください\n例: ./input/video.mov", default=default_value),
        "入力ファイル",
    )


def ask_convert_output(default_value: str) -> str:
    return require_non_empty(
        ask_text("出力ファイル名を入力してください\n例: ./output/video.mp4", default=default_value),
        "出力ファイル",
    )


def collect_convert_input(form: ConvertForm):
    input_file = ask_convert_input_file(form.input_file)
    validate_input_file_exists(input_file)
    validate_video_file_extension(input_file)

    media_info = probe_media_info(input_file)
    print("\n入力動画情報:")
    print(format_media_info_summary(media_info))
    print()

    output_file = ask_convert_output(form.output_file)
    validate_video_file_extension(output_file)
    validate_different_extension(input_file, output_file)
    validate_output_directory_exists(output_file)

    return replace(form, input_file=input_file, output_file=output_file), media_info


def build_convert_summary(form: ConvertForm, media_info) -> str:
    from pathlib import Path
    in_ext = Path(form.input_file).suffix.upper().lstrip(".")
    out_ext = Path(form.output_file).suffix.upper().lstrip(".")
    return "\n".join([
        "実行内容:",
        "- 操作: フォーマット変換（再エンコードなし）",
        f"- 入力: {form.input_file}",
        f"- 変換: {in_ext} → {out_ext}",
        f"- 出力: {form.output_file}",
    ])


def edit_convert_form(form: ConvertForm) -> ConvertForm:
    field = ask_field_to_edit([
        ("入力ファイル", "input_file"),
        ("出力ファイル", "output_file"),
    ])
    prompts = {
        "input_file": ("入力ファイルを再入力してください", "入力ファイル"),
        "output_file": ("出力ファイルを再入力してください", "出力ファイル"),
    }
    prompt, label = prompts[field]
    value = require_non_empty(ask_text(prompt, default=getattr(form, field)), label)
    return replace(form, **{field: value})


def handle_convert_review(form: ConvertForm) -> FlowResult:
    return handle_generic_review(form, ConvertForm, edit_convert_form)


def execute_convert(form: ConvertForm, dry_run: bool = False) -> None:
    command = build_convert_command(input_file=form.input_file, output_file=form.output_file)

    execute_with_output(command, form.output_file, dry_run)


def run_convert_iteration(form: ConvertForm) -> FlowResult:
    return run_generic_iteration(
        form, collect_convert_input, build_convert_summary, ConvertForm, edit_convert_form, execute_convert,
    )


def run_convert_flow() -> None:
    run_flow(ConvertForm(), run_convert_iteration)
