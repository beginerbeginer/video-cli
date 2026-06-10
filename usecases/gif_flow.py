from dataclasses import dataclass, replace

from ffmpeg.commands import build_gif_command
from ffmpeg.probe import probe_media_info
from shared.formatters import format_media_info_summary
from usecases.flow_result import FlowResult
from usecases.shared_flow import execute_with_output, handle_generic_review, run_flow, run_generic_iteration
from usecases.ui_port import UIPort
from validation.file_validators import (
    validate_gif_output_extension,
    validate_input_file_exists,
    validate_output_directory_exists,
    validate_video_file_extension,
)
from validation.value_validators import require_non_empty, validate_fps, validate_gif_width


@dataclass
class GifForm:
    input_file: str = "./input.mp4"
    fps_raw: str = "10"
    width_raw: str = "480"
    output_file: str = "./output.gif"


def collect_gif_input(form: GifForm, ui: UIPort):
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

    fps_raw = require_non_empty(
        ui.ask_text(
            "フレームレートを入力してください\n整数: 1〜60（数値が高いほど滑らか・ファイルサイズ大）\n例: 10",
            default=form.fps_raw,
        ),
        "フレームレート",
    )
    validate_fps(fps_raw, "フレームレート")

    width_raw = require_non_empty(
        ui.ask_text("幅を入力してください（高さは自動調整）\n整数: 16〜1920\n例: 480", default=form.width_raw),
        "幅",
    )
    validate_gif_width(width_raw, "幅")

    output_file = require_non_empty(
        ui.ask_text("出力ファイル名を入力してください\n例: ./output/animation.gif", default=form.output_file),
        "出力ファイル",
    )
    validate_gif_output_extension(output_file)
    validate_output_directory_exists(output_file)

    return (
        replace(form, input_file=input_file, fps_raw=fps_raw, width_raw=width_raw, output_file=output_file),
        media_info,
    )


def build_gif_summary(form: GifForm, media_info) -> str:
    source_info = "不明"
    if media_info.video:
        source_info = f"{media_info.video.width}x{media_info.video.height}"
    return "\n".join(
        [
            "実行内容:",
            "- 操作: GIF変換",
            f"- 入力: {form.input_file}",
            f"- 元サイズ: {source_info}",
            f"- フレームレート: {form.fps_raw}fps",
            f"- 出力幅: {form.width_raw}px（高さ自動）",
            f"- 出力: {form.output_file}",
        ]
    )


def edit_gif_form(form: GifForm, ui: UIPort) -> GifForm:
    field = ui.ask_menu(
        "修正したい項目を選んでください",
        [
            ("入力ファイル", "input_file"),
            ("フレームレート", "fps_raw"),
            ("幅", "width_raw"),
            ("出力ファイル", "output_file"),
        ],
    )

    prompts = {
        "input_file": ("入力ファイルを再入力してください", "入力ファイル"),
        "fps_raw": ("フレームレートを再入力してください", "フレームレート"),
        "width_raw": ("幅を再入力してください", "幅"),
        "output_file": ("出力ファイルを再入力してください", "出力ファイル"),
    }
    prompt, label = prompts[field]
    value = require_non_empty(ui.ask_text(prompt, default=getattr(form, field)), label)
    return replace(form, **{field: value})


def handle_gif_review(form: GifForm, ui: UIPort) -> FlowResult:
    return handle_generic_review(form, GifForm, lambda f: edit_gif_form(f, ui), ui)


def execute_gif(form: GifForm, dry_run: bool = False) -> None:
    fps = validate_fps(form.fps_raw, "フレームレート")
    width = validate_gif_width(form.width_raw, "幅")

    command = build_gif_command(
        input_file=form.input_file,
        output_file=form.output_file,
        fps=fps,
        width=width,
    )

    execute_with_output(command, form.output_file, dry_run)


def run_gif_iteration(form: GifForm, ui: UIPort) -> FlowResult:
    return run_generic_iteration(
        form,
        collect_gif_input,
        build_gif_summary,
        GifForm,
        edit_gif_form,
        execute_gif,
        ui,
    )


def run_gif_flow(ui: UIPort) -> None:
    run_flow(GifForm(), run_gif_iteration, ui)
