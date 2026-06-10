from dataclasses import dataclass, replace

from ffmpeg.commands import build_mute_command
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
from validation.value_validators import require_non_empty


@dataclass
class MuteForm:
    input_file: str = "./input.mp4"
    output_file: str = "./output-muted.mp4"


def collect_mute_input(form: MuteForm, ui: UIPort):
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

    output_file = require_non_empty(
        ui.ask_text("出力ファイル名を入力してください\n例: ./output/muted.mp4", default=form.output_file),
        "出力ファイル",
    )
    validate_output_directory_exists(output_file)

    return replace(form, input_file=input_file, output_file=output_file), media_info


def build_mute_summary(form: MuteForm, media_info) -> str:
    audio_info = media_info.audio.codec_name if media_info.audio else "なし"
    return "\n".join(
        [
            "実行内容:",
            "- 操作: 音声削除",
            f"- 入力: {form.input_file}",
            f"- 削除する音声コーデック: {audio_info}",
            f"- 出力: {form.output_file}",
        ]
    )


def edit_mute_form(form: MuteForm, ui: UIPort) -> MuteForm:
    field = ui.ask_menu(
        "修正したい項目を選んでください",
        [
            ("入力ファイル", "input_file"),
            ("出力ファイル", "output_file"),
        ],
    )
    prompts = {
        "input_file": ("入力ファイルを再入力してください", "入力ファイル"),
        "output_file": ("出力ファイルを再入力してください", "出力ファイル"),
    }
    prompt, label = prompts[field]
    value = require_non_empty(ui.ask_text(prompt, default=getattr(form, field)), label)
    return replace(form, **{field: value})


def handle_mute_review(form: MuteForm, ui: UIPort) -> FlowResult:
    return handle_generic_review(form, MuteForm, lambda f: edit_mute_form(f, ui), ui)


def execute_mute(form: MuteForm, dry_run: bool = False) -> None:
    command = build_mute_command(input_file=form.input_file, output_file=form.output_file)

    execute_with_output(command, form.output_file, dry_run)


def run_mute_iteration(form: MuteForm, ui: UIPort) -> FlowResult:
    return run_generic_iteration(
        form,
        collect_mute_input,
        build_mute_summary,
        MuteForm,
        edit_mute_form,
        execute_mute,
        ui,
    )


def run_mute_flow(ui: UIPort) -> None:
    run_flow(MuteForm(), run_mute_iteration, ui)
