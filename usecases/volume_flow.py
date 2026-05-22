from dataclasses import dataclass, replace

from ffmpeg.commands import build_volume_command
from ffmpeg.probe import probe_media_info
from ffmpeg.runner import run_ffmpeg
from shared.command_formatter import format_command
from shared.formatters import format_media_info_summary
from ui.prompts import ask_text, require_non_empty
from ui.review import ask_field_to_edit
from usecases.flow_result import FlowResult
from usecases.shared_flow import handle_generic_review, run_flow, run_generic_iteration
from validation.file_validators import (
    validate_input_file_exists,
    validate_output_directory_exists,
    validate_video_file_extension,
)
from validation.value_validators import validate_volume_level


@dataclass
class VolumeForm:
    input_file: str = "./input.mp4"
    volume_raw: str = "1.5"
    output_file: str = "./output-volume.mp4"


def ask_volume_input_file(default_value: str) -> str:
    return require_non_empty(
        ask_text(
            "対象の動画ファイルを入力してください\n例: ./input/video.mp4",
            default=default_value,
        ),
        "入力ファイル",
    )


def ask_volume_level(default_value: str) -> str:
    return require_non_empty(
        ask_text(
            "音量倍率を入力してください\n数値: 0.0〜10.0（1.0=元の音量、2.0=2倍、0.5=半分）\n例: 1.5",
            default=default_value,
        ),
        "音量倍率",
    )


def ask_volume_output(default_value: str) -> str:
    return require_non_empty(
        ask_text(
            "出力ファイル名を入力してください\n例: ./output/volume-adjusted.mp4",
            default=default_value,
        ),
        "出力ファイル",
    )


def collect_volume_input(form: VolumeForm):
    input_file = ask_volume_input_file(form.input_file)
    validate_input_file_exists(input_file)
    validate_video_file_extension(input_file)

    media_info = probe_media_info(input_file)
    print("\n入力動画情報:")
    print(format_media_info_summary(media_info))
    print()

    volume_raw = ask_volume_level(form.volume_raw)
    validate_volume_level(volume_raw, "音量倍率")

    output_file = ask_volume_output(form.output_file)
    validate_output_directory_exists(output_file)

    return replace(
        form,
        input_file=input_file,
        volume_raw=volume_raw,
        output_file=output_file,
    ), media_info


def build_volume_summary(form: VolumeForm, media_info) -> str:
    current_volume = "不明"
    if media_info.audio:
        current_volume = media_info.audio.codec_name
    return "\n".join(
        [
            "実行内容:",
            "- 操作: 音量調整",
            f"- 入力: {form.input_file}",
            f"- 音声コーデック: {current_volume}",
            f"- 音量倍率: {form.volume_raw}",
            f"- 出力: {form.output_file}",
        ]
    )


def edit_volume_form(form: VolumeForm) -> VolumeForm:
    field = ask_field_to_edit(
        [
            ("入力ファイル", "input_file"),
            ("音量倍率", "volume_raw"),
            ("出力ファイル", "output_file"),
        ]
    )

    prompts = {
        "input_file": ("入力ファイルを再入力してください", "入力ファイル"),
        "volume_raw": ("音量倍率を再入力してください", "音量倍率"),
        "output_file": ("出力ファイルを再入力してください", "出力ファイル"),
    }
    prompt, label = prompts[field]
    value = require_non_empty(ask_text(prompt, default=getattr(form, field)), label)
    return replace(form, **{field: value})


def handle_volume_review(form: VolumeForm) -> FlowResult:
    return handle_generic_review(form, VolumeForm, edit_volume_form)


def execute_volume(form: VolumeForm, dry_run: bool = False) -> None:
    volume_level = validate_volume_level(form.volume_raw, "音量倍率")

    command = build_volume_command(
        input_file=form.input_file,
        output_file=form.output_file,
        volume_level=volume_level,
    )

    print("生成された FFmpeg コマンド:")
    print(format_command(command))
    print()

    result = run_ffmpeg(command, dry_run=dry_run)

    if result.executed:
        print(f"完了: {form.output_file}")
    else:
        print("ドライラン完了: 実行はしていません。")


def run_volume_iteration(form: VolumeForm) -> FlowResult:
    return run_generic_iteration(
        form,
        collect_volume_input,
        build_volume_summary,
        VolumeForm,
        edit_volume_form,
        execute_volume,
    )


def run_volume_flow() -> None:
    run_flow(VolumeForm(), run_volume_iteration)
