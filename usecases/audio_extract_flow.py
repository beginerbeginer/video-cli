from dataclasses import dataclass, replace

from ffmpeg.commands import build_audio_extract_command
from ffmpeg.probe import probe_media_info
from ffmpeg.runner import run_ffmpeg
from shared.command_formatter import format_command
from shared.formatters import format_media_info_summary
from ui.prompts import ask_text, require_non_empty
from ui.review import ask_field_to_edit
from usecases.flow_result import FlowResult
from usecases.shared_flow import handle_generic_review, run_flow, run_generic_iteration
from validation.file_validators import (
    validate_audio_output_extension,
    validate_input_file_exists,
    validate_output_directory_exists,
    validate_video_file_extension,
)


@dataclass
class AudioExtractForm:
    input_file: str = "./input.mp4"
    output_file: str = "./output-audio.mp3"


def ask_audio_extract_input_file(default_value: str) -> str:
    return require_non_empty(
        ask_text(
            "対象の動画ファイルを入力してください\n例: ./input/video.mp4",
            default=default_value,
        ),
        "入力ファイル",
    )


def ask_audio_extract_output(default_value: str) -> str:
    return require_non_empty(
        ask_text(
            "出力ファイル名を入力してください\n拡張子で形式を指定: .mp3 / .aac / .wav / .m4a\n例: ./output/audio.mp3",
            default=default_value,
        ),
        "出力ファイル",
    )


def collect_audio_extract_input(form: AudioExtractForm):
    input_file = ask_audio_extract_input_file(form.input_file)
    validate_input_file_exists(input_file)
    validate_video_file_extension(input_file)

    media_info = probe_media_info(input_file)
    print("\n入力動画情報:")
    print(format_media_info_summary(media_info))
    print()

    output_file = ask_audio_extract_output(form.output_file)
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


def edit_audio_extract_form(form: AudioExtractForm) -> AudioExtractForm:
    field = ask_field_to_edit(
        [
            ("入力ファイル", "input_file"),
            ("出力ファイル", "output_file"),
        ]
    )

    prompts = {
        "input_file": ("入力ファイルを再入力してください", "入力ファイル"),
        "output_file": ("出力ファイルを再入力してください", "出力ファイル"),
    }
    prompt, label = prompts[field]
    value = require_non_empty(ask_text(prompt, default=getattr(form, field)), label)
    return replace(form, **{field: value})


def handle_audio_extract_review(form: AudioExtractForm) -> FlowResult:
    return handle_generic_review(form, AudioExtractForm, edit_audio_extract_form)


def execute_audio_extract(form: AudioExtractForm, dry_run: bool = False) -> None:
    command = build_audio_extract_command(
        input_file=form.input_file,
        output_file=form.output_file,
    )

    print("生成された FFmpeg コマンド:")
    print(format_command(command))
    print()

    result = run_ffmpeg(command, dry_run=dry_run)

    if result.executed:
        print(f"完了: {form.output_file}")
    else:
        print("ドライラン完了: 実行はしていません。")


def run_audio_extract_iteration(form: AudioExtractForm) -> FlowResult:
    return run_generic_iteration(
        form,
        collect_audio_extract_input,
        build_audio_extract_summary,
        AudioExtractForm,
        edit_audio_extract_form,
        execute_audio_extract,
    )


def run_audio_extract_flow() -> None:
    run_flow(AudioExtractForm(), run_audio_extract_iteration)
