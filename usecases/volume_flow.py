from dataclasses import dataclass, replace

from domain.media_info import MediaInfo
from ffmpeg.commands import build_volume_command
from ffmpeg.probe import probe_media_info
from shared.formatters import format_media_info_summary
from usecases.flow_result import FlowResult
from usecases.form_validation import form_field, require_field, validate_output_path, validate_video_input_path
from usecases.shared_flow import execute_with_output, handle_generic_review, run_flow, run_generic_iteration
from usecases.ui_port import UIPort
from validation.value_validators import require_non_empty, validate_volume_level


@dataclass
class VolumeForm:
    input_file: str = "./input.mp4"
    volume_raw: str = "1.5"
    output_file: str = "./output-volume.mp4"


def validate_volume_input_file(input_file: str) -> MediaInfo:
    validate_video_input_path(input_file)
    with form_field("input_file"):
        return probe_media_info(input_file)


def validate_volume_raw(raw: str) -> float:
    require_field(raw, "音量倍率", "volume_raw")
    with form_field("volume_raw"):
        return validate_volume_level(raw, "音量倍率")


def validate_volume_output_file(output_file: str) -> None:
    validate_output_path(output_file)


def validate_volume_form(form: VolumeForm) -> MediaInfo:
    media_info = validate_volume_input_file(form.input_file)
    validate_volume_raw(form.volume_raw)
    validate_volume_output_file(form.output_file)
    return media_info


def build_volume_command_from_form(form: VolumeForm) -> list[str]:
    return build_volume_command(
        input_file=form.input_file,
        output_file=form.output_file,
        volume_level=validate_volume_raw(form.volume_raw),
    )


def collect_volume_input(form: VolumeForm, ui: UIPort):
    # validate_volume_form を最後にまとめて呼ばないのは、CLI では入力ファイルの誤りを
    # 次の項目を聞く前に知らせたいため。段階ごとの検証関数を聞いた直後に呼ぶ。
    input_file = ui.ask_text("対象の動画ファイルを入力してください\n例: ./input/video.mp4", default=form.input_file)
    media_info = validate_volume_input_file(input_file)
    print("\n入力動画情報:")
    print(format_media_info_summary(media_info))
    print()

    volume_raw = ui.ask_text(
        "音量倍率を入力してください\n数値: 0.0〜10.0（1.0=元の音量、2.0=2倍、0.5=半分）\n例: 1.5",
        default=form.volume_raw,
    )
    validate_volume_raw(volume_raw)

    output_file = ui.ask_text(
        "出力ファイル名を入力してください\n例: ./output/volume-adjusted.mp4", default=form.output_file
    )
    validate_volume_output_file(output_file)

    return replace(form, input_file=input_file, volume_raw=volume_raw, output_file=output_file), media_info


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


def edit_volume_form(form: VolumeForm, ui: UIPort) -> VolumeForm:
    field = ui.ask_menu(
        "修正したい項目を選んでください",
        [
            ("入力ファイル", "input_file"),
            ("音量倍率", "volume_raw"),
            ("出力ファイル", "output_file"),
        ],
    )

    prompts = {
        "input_file": ("入力ファイルを再入力してください", "入力ファイル"),
        "volume_raw": ("音量倍率を再入力してください", "音量倍率"),
        "output_file": ("出力ファイルを再入力してください", "出力ファイル"),
    }
    prompt, label = prompts[field]
    value = require_non_empty(ui.ask_text(prompt, default=getattr(form, field)), label)
    return replace(form, **{field: value})


def handle_volume_review(form: VolumeForm, ui: UIPort) -> FlowResult:
    return handle_generic_review(form, VolumeForm, lambda f: edit_volume_form(f, ui), ui)


def execute_volume(form: VolumeForm, dry_run: bool = False) -> None:
    execute_with_output(build_volume_command_from_form(form), form.output_file, dry_run)


def run_volume_iteration(form: VolumeForm, ui: UIPort) -> FlowResult:
    return run_generic_iteration(
        form,
        collect_volume_input,
        build_volume_summary,
        VolumeForm,
        edit_volume_form,
        execute_volume,
        ui,
    )


def run_volume_flow(ui: UIPort) -> None:
    run_flow(VolumeForm(), run_volume_iteration, ui)
