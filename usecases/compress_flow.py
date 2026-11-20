from dataclasses import dataclass, replace

from domain.media_info import MediaInfo
from ffmpeg.commands import build_compress_command
from ffmpeg.probe import probe_media_info
from shared.formatters import format_media_info_summary
from usecases.flow_result import FlowResult
from usecases.form_validation import form_field, require_field, validate_output_path, validate_video_input_path
from usecases.shared_flow import execute_with_output, handle_generic_review, run_flow, run_generic_iteration
from usecases.ui_port import UIPort
from validation.file_validators import validate_compress_output_extension
from validation.value_validators import require_non_empty, validate_crf


@dataclass
class CompressForm:
    input_file: str = "./input.mp4"
    crf_raw: str = "23"
    output_file: str = "./output-compressed.mp4"


def validate_compress_input_file(input_file: str) -> MediaInfo:
    validate_video_input_path(input_file)
    with form_field("input_file"):
        return probe_media_info(input_file)


def validate_crf_raw(raw: str) -> int:
    require_field(raw, "CRF 値", "crf_raw")
    with form_field("crf_raw"):
        return validate_crf(raw, "CRF 値")


def validate_compress_output_file(output_file: str) -> None:
    validate_output_path(output_file)
    with form_field("output_file"):
        validate_compress_output_extension(output_file)


def validate_compress_form(form: CompressForm) -> MediaInfo:
    media_info = validate_compress_input_file(form.input_file)
    validate_crf_raw(form.crf_raw)
    validate_compress_output_file(form.output_file)
    return media_info


def build_compress_command_from_form(form: CompressForm) -> list[str]:
    return build_compress_command(
        input_file=form.input_file,
        output_file=form.output_file,
        crf=validate_crf_raw(form.crf_raw),
    )


def collect_compress_input(form: CompressForm, ui: UIPort):
    # validate_compress_form を最後にまとめて呼ばないのは、CLI では入力ファイルの誤りを
    # 次の項目を聞く前に知らせたいため。段階ごとの検証関数を聞いた直後に呼ぶ。
    input_file = ui.ask_text("対象の動画ファイルを入力してください\n例: ./input/video.mp4", default=form.input_file)
    media_info = validate_compress_input_file(input_file)
    print("\n入力動画情報:")
    print(format_media_info_summary(media_info))
    print()

    crf_raw = ui.ask_text(
        "CRF 値を入力してください\n範囲: 0〜51（低いほど高画質・大サイズ、デフォルト: 23）\n例: 23",
        default=form.crf_raw,
    )
    validate_crf_raw(crf_raw)

    output_file = ui.ask_text("出力ファイル名を入力してください\n例: ./output/compressed.mp4", default=form.output_file)
    validate_compress_output_file(output_file)

    return replace(form, input_file=input_file, crf_raw=crf_raw, output_file=output_file), media_info


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


def edit_compress_form(form: CompressForm, ui: UIPort) -> CompressForm:
    field = ui.ask_menu(
        "修正したい項目を選んでください",
        [
            ("入力ファイル", "input_file"),
            ("CRF 値", "crf_raw"),
            ("出力ファイル", "output_file"),
        ],
    )

    prompts = {
        "input_file": ("入力ファイルを再入力してください", "入力ファイル"),
        "crf_raw": ("CRF 値を再入力してください", "CRF 値"),
        "output_file": ("出力ファイルを再入力してください", "出力ファイル"),
    }
    prompt, label = prompts[field]
    value = require_non_empty(ui.ask_text(prompt, default=getattr(form, field)), label)
    return replace(form, **{field: value})


def handle_compress_review(form: CompressForm, ui: UIPort) -> FlowResult:
    return handle_generic_review(form, CompressForm, lambda f: edit_compress_form(f, ui), ui)


def execute_compress(form: CompressForm, dry_run: bool = False) -> None:
    execute_with_output(build_compress_command_from_form(form), form.output_file, dry_run)


def run_compress_iteration(form: CompressForm, ui: UIPort) -> FlowResult:
    return run_generic_iteration(
        form,
        collect_compress_input,
        build_compress_summary,
        CompressForm,
        edit_compress_form,
        execute_compress,
        ui,
    )


def run_compress_flow(ui: UIPort) -> None:
    run_flow(CompressForm(), run_compress_iteration, ui)
