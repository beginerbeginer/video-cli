from dataclasses import dataclass, field, replace

from ffmpeg.commands import create_concat_list_file
from ffmpeg.concat_strategy import choose_concat_strategy
from ffmpeg.probe import probe_media_info
from shared.errors import ValidationError
from shared.formatters import format_media_info_summary
from usecases.flow_result import FlowResult
from usecases.shared_flow import execute_with_output, run_flow, run_generic_iteration
from usecases.ui_port import UIPort
from validation.file_validators import (
    validate_input_file_exists,
    validate_output_directory_exists,
    validate_video_file_extension,
)
from validation.media_validators import (
    are_concat_streams_compatible,
    build_concat_compatibility_report,
)
from validation.value_validators import require_non_empty


@dataclass
class ConcatForm:
    count_raw: str = "2"
    input_files: list[str] = field(default_factory=list)
    output_file: str = "./output-merged.mp4"


def parse_concat_count(count_raw: str) -> int:
    try:
        count = int(count_raw)
    except ValueError as exc:
        raise ValidationError("結合本数は 2 以上の整数で入力してください。") from exc
    if count < 2:
        raise ValidationError("結合本数は 2 以上の整数で入力してください。")
    return count


def collect_concat_files(form: ConcatForm, count: int, ui: UIPort) -> list[str]:
    input_files: list[str] = []
    for index in range(count):
        default_value = form.input_files[index] if index < len(form.input_files) else None
        file_path = require_non_empty(
            ui.ask_text(
                f"結合する動画ファイル {index + 1} を入力してください\n例: ./videos/part{index + 1}.mp4",
                default=default_value,
            ),
            f"入力ファイル{index + 1}",
        )
        validate_input_file_exists(file_path)
        validate_video_file_extension(file_path)
        input_files.append(file_path)
    return input_files


def collect_concat_input(form: ConcatForm, ui: UIPort):
    count_raw = require_non_empty(
        ui.ask_text("何本の動画を結合しますか？\n2以上の整数を入力してください", default=form.count_raw),
        "結合本数",
    )
    count = parse_concat_count(count_raw)
    input_files = collect_concat_files(form, count, ui)

    output_file = require_non_empty(
        ui.ask_text("出力ファイル名を入力してください\n例: ./output/merged.mp4", default=form.output_file),
        "出力ファイル",
    )
    validate_output_directory_exists(output_file)

    media_infos = [probe_media_info(path) for path in input_files]
    compatible = are_concat_streams_compatible(media_infos)

    return (
        replace(form, count_raw=count_raw, input_files=input_files, output_file=output_file),
        media_infos,
        compatible,
    )


def format_media_info_block(media_info) -> str:
    return format_media_info_summary(media_info).replace(chr(10), chr(10) + "  ")


def build_concat_summary(form: ConcatForm, media_infos, compatible: bool) -> str:
    lines = [
        "実行内容:",
        "- 操作: 動画の結合",
        f"- 入力本数: {len(form.input_files)}",
    ]
    for index, media_info in enumerate(media_infos, start=1):
        lines.extend([f"- 入力{index}: {media_info.path}", f"  {format_media_info_block(media_info)}"])
    lines.extend(
        [
            f"- 出力: {form.output_file}",
            "- 結合方式: " + ("copy" if compatible else "再エンコード"),
            "",
            build_concat_compatibility_report(media_infos),
        ]
    )
    return "\n".join(lines)


def update_concat_file(input_files: list[str], index: int, value: str) -> list[str]:
    updated = list(input_files)
    while len(updated) <= index:
        updated.append("")
    updated[index] = value
    return updated


def edit_concat_form(form: ConcatForm, ui: UIPort) -> ConcatForm:
    fields = [("結合本数", "count_raw")]
    fields.extend((f"入力ファイル{i + 1}", f"input_{i}") for i in range(max(1, len(form.input_files))))
    fields.append(("出力ファイル", "output_file"))

    field = ui.ask_menu("修正したい項目を選んでください", fields)

    if field == "count_raw":
        value = require_non_empty(
            ui.ask_text("結合本数を再入力してください", default=form.count_raw), "結合本数"
        )
        return replace(form, count_raw=value)

    if field == "output_file":
        value = require_non_empty(
            ui.ask_text("出力ファイルを再入力してください", default=form.output_file), "出力ファイル"
        )
        return replace(form, output_file=value)

    index = int(field.split("_")[1])
    default_value = form.input_files[index] if index < len(form.input_files) else None
    value = require_non_empty(
        ui.ask_text(f"入力ファイル{index + 1}を再入力してください", default=default_value),
        f"入力ファイル{index + 1}",
    )
    return replace(form, input_files=update_concat_file(form.input_files, index, value))


def build_concat_command(form: ConcatForm, compatible: bool, concat_list_file: str) -> list[str]:
    strategy = choose_concat_strategy(compatible)
    return strategy.build(concat_list_file, form.output_file)


def execute_concat(form: ConcatForm, compatible: bool, dry_run: bool = False) -> None:
    with create_concat_list_file(form.input_files) as concat_list_file:
        command = build_concat_command(form, compatible, concat_list_file)
        execute_with_output(command, form.output_file, dry_run)


def run_concat_iteration(form: ConcatForm, ui: UIPort) -> FlowResult:
    compatible_ref: list = [None]

    def collect_with_capture(f, u):
        result = collect_concat_input(f, u)
        compatible_ref[0] = result[2]
        return result

    def execute_fn(f, dry_run):
        execute_concat(f, compatible_ref[0], dry_run=dry_run)

    return run_generic_iteration(
        form,
        collect_with_capture,
        build_concat_summary,
        ConcatForm,
        edit_concat_form,
        execute_fn,
        ui,
    )


def run_concat_flow(ui: UIPort) -> None:
    run_flow(ConcatForm(), run_concat_iteration, ui)
