from dataclasses import dataclass, replace

from ffmpeg.commands import build_gif_command
from ffmpeg.probe import probe_media_info
from ffmpeg.runner import run_ffmpeg
from shared.command_formatter import format_command
from shared.formatters import format_media_info_summary
from ui.prompts import ask_text, require_non_empty
from ui.review import ask_field_to_edit
from usecases.flow_result import FlowResult
from usecases.shared_flow import handle_generic_review, run_flow, run_generic_iteration
from validation.file_validators import (
    validate_gif_output_extension,
    validate_input_file_exists,
    validate_output_directory_exists,
    validate_video_file_extension,
)
from validation.value_validators import validate_fps, validate_gif_width


@dataclass
class GifForm:
    input_file: str = "./input.mp4"
    fps_raw: str = "10"
    width_raw: str = "480"
    output_file: str = "./output.gif"


def ask_gif_input_file(default_value: str) -> str:
    return require_non_empty(
        ask_text(
            "対象の動画ファイルを入力してください\n例: ./input/video.mp4",
            default=default_value,
        ),
        "入力ファイル",
    )


def ask_gif_fps(default_value: str) -> str:
    return require_non_empty(
        ask_text(
            "フレームレートを入力してください\n整数: 1〜60（数値が高いほど滑らか・ファイルサイズ大）\n例: 10",
            default=default_value,
        ),
        "フレームレート",
    )


def ask_gif_width(default_value: str) -> str:
    return require_non_empty(
        ask_text(
            "幅を入力してください（高さは自動調整）\n整数: 16〜1920\n例: 480",
            default=default_value,
        ),
        "幅",
    )


def ask_gif_output(default_value: str) -> str:
    return require_non_empty(
        ask_text(
            "出力ファイル名を入力してください\n例: ./output/animation.gif",
            default=default_value,
        ),
        "出力ファイル",
    )


def collect_gif_input(form: GifForm):
    input_file = ask_gif_input_file(form.input_file)
    validate_input_file_exists(input_file)
    validate_video_file_extension(input_file)

    media_info = probe_media_info(input_file)
    print("\n入力動画情報:")
    print(format_media_info_summary(media_info))
    print()

    fps_raw = ask_gif_fps(form.fps_raw)
    validate_fps(fps_raw, "フレームレート")

    width_raw = ask_gif_width(form.width_raw)
    validate_gif_width(width_raw, "幅")

    output_file = ask_gif_output(form.output_file)
    validate_gif_output_extension(output_file)
    validate_output_directory_exists(output_file)

    return replace(
        form,
        input_file=input_file,
        fps_raw=fps_raw,
        width_raw=width_raw,
        output_file=output_file,
    ), media_info


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


def edit_gif_form(form: GifForm) -> GifForm:
    field = ask_field_to_edit(
        [
            ("入力ファイル", "input_file"),
            ("フレームレート", "fps_raw"),
            ("幅", "width_raw"),
            ("出力ファイル", "output_file"),
        ]
    )

    prompts = {
        "input_file": ("入力ファイルを再入力してください", "入力ファイル"),
        "fps_raw": ("フレームレートを再入力してください", "フレームレート"),
        "width_raw": ("幅を再入力してください", "幅"),
        "output_file": ("出力ファイルを再入力してください", "出力ファイル"),
    }
    prompt, label = prompts[field]
    value = require_non_empty(ask_text(prompt, default=getattr(form, field)), label)
    return replace(form, **{field: value})


def handle_gif_review(form: GifForm) -> FlowResult:
    return handle_generic_review(form, GifForm, edit_gif_form)


def execute_gif(form: GifForm, dry_run: bool = False) -> None:
    fps = validate_fps(form.fps_raw, "フレームレート")
    width = validate_gif_width(form.width_raw, "幅")

    command = build_gif_command(
        input_file=form.input_file,
        output_file=form.output_file,
        fps=fps,
        width=width,
    )

    print("生成された FFmpeg コマンド:")
    print(format_command(command))
    print()

    result = run_ffmpeg(command, dry_run=dry_run)

    if result.executed:
        print(f"完了: {form.output_file}")
    else:
        print("ドライラン完了: 実行はしていません。")


def run_gif_iteration(form: GifForm) -> FlowResult:
    return run_generic_iteration(
        form,
        collect_gif_input,
        build_gif_summary,
        GifForm,
        edit_gif_form,
        execute_gif,
    )


def run_gif_flow() -> None:
    run_flow(GifForm(), run_gif_iteration)
