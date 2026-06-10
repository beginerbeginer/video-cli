from dataclasses import dataclass, replace

from ffmpeg.commands import build_thumbnail_command
from ffmpeg.probe import probe_media_info
from shared.formatters import format_media_info_summary
from usecases.flow_result import FlowResult
from usecases.shared_flow import execute_with_output, handle_generic_review, run_flow, run_generic_iteration
from usecases.ui_port import UIPort
from validation.file_validators import (
    validate_image_output_extension,
    validate_input_file_exists,
    validate_output_directory_exists,
    validate_video_file_extension,
)
from validation.value_validators import parse_time_input, require_non_empty, validate_timestamp_within_duration


@dataclass
class ThumbnailForm:
    input_file: str = "./input.mp4"
    timestamp_raw: str = "0"
    output_file: str = "./output-thumbnail.jpg"


def collect_thumbnail_input(form: ThumbnailForm, ui: UIPort):
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

    duration = media_info.duration_seconds
    timestamp_raw = require_non_empty(
        ui.ask_text(
            f"取り出す秒数を入力してください\nHH:MM:SS または秒数 / 動画の長さ: {duration:.0f}秒\n例: 10",
            default=form.timestamp_raw,
        ),
        "秒数",
    )
    validate_timestamp_within_duration(timestamp_raw, duration)

    output_file = require_non_empty(
        ui.ask_text(
            "出力ファイル名を入力してください\n拡張子で形式を指定: .jpg / .jpeg / .png\n例: ./output/thumbnail.jpg",
            default=form.output_file,
        ),
        "出力ファイル",
    )
    validate_image_output_extension(output_file)
    validate_output_directory_exists(output_file)

    return replace(form, input_file=input_file, timestamp_raw=timestamp_raw, output_file=output_file), media_info


def build_thumbnail_summary(form: ThumbnailForm, media_info) -> str:
    resolution = "不明"
    if media_info.video:
        resolution = f"{media_info.video.width}x{media_info.video.height}"
    return "\n".join(
        [
            "実行内容:",
            "- 操作: サムネイル抽出",
            f"- 入力: {form.input_file}",
            f"- 解像度: {resolution}",
            f"- 取り出し秒数: {form.timestamp_raw}",
            f"- 出力: {form.output_file}",
        ]
    )


def edit_thumbnail_form(form: ThumbnailForm, ui: UIPort) -> ThumbnailForm:
    field = ui.ask_menu(
        "修正したい項目を選んでください",
        [
            ("入力ファイル", "input_file"),
            ("取り出し秒数", "timestamp_raw"),
            ("出力ファイル", "output_file"),
        ],
    )

    prompts = {
        "input_file": ("入力ファイルを再入力してください", "入力ファイル"),
        "timestamp_raw": ("取り出し秒数を再入力してください", "取り出し秒数"),
        "output_file": ("出力ファイルを再入力してください", "出力ファイル"),
    }
    prompt, label = prompts[field]
    value = require_non_empty(ui.ask_text(prompt, default=getattr(form, field)), label)
    return replace(form, **{field: value})


def handle_thumbnail_review(form: ThumbnailForm, ui: UIPort) -> FlowResult:
    return handle_generic_review(form, ThumbnailForm, lambda f: edit_thumbnail_form(f, ui), ui)


def execute_thumbnail(form: ThumbnailForm, dry_run: bool = False) -> None:
    timestamp_seconds = parse_time_input(form.timestamp_raw)

    command = build_thumbnail_command(
        input_file=form.input_file,
        output_file=form.output_file,
        timestamp_seconds=timestamp_seconds,
    )

    execute_with_output(command, form.output_file, dry_run)


def run_thumbnail_iteration(form: ThumbnailForm, ui: UIPort) -> FlowResult:
    return run_generic_iteration(
        form,
        collect_thumbnail_input,
        build_thumbnail_summary,
        ThumbnailForm,
        edit_thumbnail_form,
        execute_thumbnail,
        ui,
    )


def run_thumbnail_flow(ui: UIPort) -> None:
    run_flow(ThumbnailForm(), run_thumbnail_iteration, ui)
