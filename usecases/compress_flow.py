from dataclasses import dataclass, replace

from ffmpeg.commands import build_compress_command
from ffmpeg.probe import probe_media_info
from shared.formatters import format_media_info_summary
from ui.prompts import ask_text, require_non_empty
from ui.review import ask_field_to_edit
from usecases.flow_result import FlowResult
from usecases.shared_flow import execute_with_output, handle_generic_review, run_flow, run_generic_iteration
from validation.file_validators import (
    validate_compress_output_extension,
    validate_input_file_exists,
    validate_output_directory_exists,
    validate_video_file_extension,
)
from validation.value_validators import validate_crf


@dataclass
class CompressForm:
    input_file: str = "./input.mp4"
    crf_raw: str = "23"
    output_file: str = "./output-compressed.mp4"


def ask_compress_input_file(default_value: str) -> str:
    return require_non_empty(
        ask_text(
            "対象の動画ファイルを入力してください\n例: ./input/video.mp4",
            default=default_value,
        ),
        "入力ファイル",
    )


def ask_crf(default_value: str) -> str:
    return require_non_empty(
        ask_text(
            "CRF 値を入力してください\n範囲: 0〜51（低いほど高画質・大サイズ、デフォルト: 23）\n例: 23",
            default=default_value,
        ),
        "CRF 値",
    )


def ask_compress_output(default_value: str) -> str:
    return require_non_empty(
        ask_text(
            "出力ファイル名を入力してください\n例: ./output/compressed.mp4",
            default=default_value,
        ),
        "出力ファイル",
    )


def collect_compress_input(form: CompressForm):
    input_file = ask_compress_input_file(form.input_file)
    validate_input_file_exists(input_file)
    validate_video_file_extension(input_file)

    media_info = probe_media_info(input_file)
    print("\n入力動画情報:")
    print(format_media_info_summary(media_info))
    print()

    crf_raw = ask_crf(form.crf_raw)
    validate_crf(crf_raw, "CRF 値")

    output_file = ask_compress_output(form.output_file)
    validate_output_directory_exists(output_file)
    validate_compress_output_extension(output_file)

    return replace(
        form,
        input_file=input_file,
        crf_raw=crf_raw,
        output_file=output_file,
    ), media_info


def build_compress_summary(form: CompressForm, media_info) -> str:
    return "\n".join(
        [
            "実行内容:",
            "- 操作: 動画圧縮（H.264/CRF）",
            f"- 入力: {form.input_file}",
            f"- CRF 値: {form.crf_raw}（低いほど高画質）",
            f"- 出力: {form.output_file}",
        ]
    )


def edit_compress_form(form: CompressForm) -> CompressForm:
    field = ask_field_to_edit(
        [
            ("入力ファイル", "input_file"),
            ("CRF 値", "crf_raw"),
            ("出力ファイル", "output_file"),
        ]
    )

    prompts = {
        "input_file": ("入力ファイルを再入力してください", "入力ファイル"),
        "crf_raw": ("CRF 値を再入力してください", "CRF 値"),
        "output_file": ("出力ファイルを再入力してください", "出力ファイル"),
    }
    prompt, label = prompts[field]
    value = require_non_empty(ask_text(prompt, default=getattr(form, field)), label)
    return replace(form, **{field: value})


def handle_compress_review(form: CompressForm) -> FlowResult:
    return handle_generic_review(form, CompressForm, edit_compress_form)


def execute_compress(form: CompressForm, dry_run: bool = False) -> None:
    crf = validate_crf(form.crf_raw, "CRF 値")

    command = build_compress_command(
        input_file=form.input_file,
        output_file=form.output_file,
        crf=crf,
    )

    execute_with_output(command, form.output_file, dry_run)


def run_compress_iteration(form: CompressForm) -> FlowResult:
    return run_generic_iteration(
        form,
        collect_compress_input,
        build_compress_summary,
        CompressForm,
        edit_compress_form,
        execute_compress,
    )


def run_compress_flow() -> None:
    run_flow(CompressForm(), run_compress_iteration)
