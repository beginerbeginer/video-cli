from dataclasses import dataclass, replace

from ffmpeg.commands import build_audio_extract_command
from ffmpeg.probe import probe_media_info
from shared.formatters import format_media_info_summary
from usecases.flow_result import FlowResult
from usecases.shared_flow import execute_with_output, handle_generic_review, run_flow, run_generic_iteration
from usecases.ui_port import UIPort
from validation.file_validators import (
    validate_audio_output_extension,
    validate_input_file_exists,
    validate_output_directory_exists,
    validate_video_file_extension,
)
from validation.value_validators import require_non_empty


@dataclass
class AudioExtractForm:
    input_file: str = "./input.mp4"
    output_file: str = "./output-audio.mp3"


def collect_audio_extract_input(form: AudioExtractForm, ui: UIPort):
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
        ui.ask_text(
            "出力ファイル名を入力してください\n拡張子で形式を指定: .mp3 / .aac / .wav / .m4a\n例: ./output/audio.mp3",
            default=form.output_file,
        ),
        "出力ファイル",
    )
    validate_audio_output_extension(output_file)
    validate_output_directory_exists(output_file)

    return replace(form, input_file=input_file, output_file=output_file), media_info


def build_audio_extract_summary(form: AudioExtractForm, media_info) -> str:
    audio_codec = media_info.audio.codec_name if media_info.audio else "不明"
    return "\n".join(
        [
            "実行内容:",
            "- 操作: 音声抽出",
            f"- 入力: {form.input_file}",
            f"- 音声コーデック: {audio_codec}",
            f"- 出力: {form.output_file}",
        ]
    )


def edit_audio_extract_form(form: AudioExtractForm, ui: UIPort) -> AudioExtractForm:
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


def handle_audio_extract_review(form: AudioExtractForm, ui: UIPort) -> FlowResult:
    return handle_generic_review(form, AudioExtractForm, lambda f: edit_audio_extract_form(f, ui), ui)


def execute_audio_extract(form: AudioExtractForm, dry_run: bool = False) -> None:
    command = build_audio_extract_command(
        input_file=form.input_file,
        output_file=form.output_file,
    )

    execute_with_output(command, form.output_file, dry_run)


def run_audio_extract_iteration(form: AudioExtractForm, ui: UIPort) -> FlowResult:
    return run_generic_iteration(
        form,
        collect_audio_extract_input,
        build_audio_extract_summary,
        AudioExtractForm,
        edit_audio_extract_form,
        execute_audio_extract,
        ui,
    )


def run_audio_extract_flow(ui: UIPort) -> None:
    run_flow(AudioExtractForm(), run_audio_extract_iteration, ui)
