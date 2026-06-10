from dataclasses import dataclass, replace

from ffmpeg.commands import build_fps_command
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
from validation.value_validators import require_non_empty, validate_fps_rate


@dataclass
class FpsForm:
    input_file: str = "./input.mp4"
    fps_raw: str = "30"
    output_file: str = "./output-fps.mp4"


def collect_fps_input(form: FpsForm, ui: UIPort):
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
            "フレームレートを入力してください\n範囲: 1〜120（小数対応、例: 23.976）\n例: 30",
            default=form.fps_raw,
        ),
        "フレームレート",
    )
    validate_fps_rate(fps_raw, "フレームレート")

    output_file = require_non_empty(
        ui.ask_text("出力ファイル名を入力してください\n例: ./output/video-30fps.mp4", default=form.output_file),
        "出力ファイル",
    )
    validate_output_directory_exists(output_file)
    validate_video_file_extension(output_file)

    return replace(form, input_file=input_file, fps_raw=fps_raw, output_file=output_file), media_info


def build_fps_summary(form: FpsForm, media_info) -> str:
    return "\n".join(
        [
            "実行内容:",
            "- 操作: フレームレート変換",
            f"- 入力: {form.input_file}",
            f"- フレームレート: {form.fps_raw} fps",
            f"- 出力: {form.output_file}",
        ]
    )


def edit_fps_form(form: FpsForm, ui: UIPort) -> FpsForm:
    field = ui.ask_menu(
        "修正したい項目を選んでください",
        [
            ("入力ファイル", "input_file"),
            ("フレームレート", "fps_raw"),
            ("出力ファイル", "output_file"),
        ],
    )

    prompts = {
        "input_file": ("入力ファイルを再入力してください", "入力ファイル"),
        "fps_raw": ("フレームレートを再入力してください", "フレームレート"),
        "output_file": ("出力ファイルを再入力してください", "出力ファイル"),
    }
    prompt, label = prompts[field]
    value = require_non_empty(ui.ask_text(prompt, default=getattr(form, field)), label)
    return replace(form, **{field: value})


def handle_fps_review(form: FpsForm, ui: UIPort) -> FlowResult:
    return handle_generic_review(form, FpsForm, lambda f: edit_fps_form(f, ui), ui)


def execute_fps(form: FpsForm, dry_run: bool = False) -> None:
    fps = validate_fps_rate(form.fps_raw, "フレームレート")

    command = build_fps_command(
        input_file=form.input_file,
        output_file=form.output_file,
        fps=fps,
    )

    execute_with_output(command, form.output_file, dry_run)


def run_fps_iteration(form: FpsForm, ui: UIPort) -> FlowResult:
    return run_generic_iteration(
        form,
        collect_fps_input,
        build_fps_summary,
        FpsForm,
        edit_fps_form,
        execute_fps,
        ui,
    )


def run_fps_flow(ui: UIPort) -> None:
    run_flow(FpsForm(), run_fps_iteration, ui)
