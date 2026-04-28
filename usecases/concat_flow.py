from dataclasses import dataclass, field, replace
from pathlib import Path

from ffmpeg.commands import create_concat_list_file
from ffmpeg.concat_strategy import choose_concat_strategy
from ffmpeg.probe import probe_media_info
from ffmpeg.runner import run_ffmpeg
from shared.command_formatter import format_command
from shared.errors import ValidationError
from shared.formatters import format_media_info_summary
from ui.prompts import ask_text, require_non_empty
from ui.review import ask_field_to_edit, ask_review_action
from ui.review_actions import build_review_action_handlers
from usecases.flow_result import FLOW_RESULT_FACTORIES, FlowResult
from validation.file_validators import (
    validate_input_file_exists,
    validate_output_directory_exists,
    validate_video_file_extension,
)
from validation.media_validators import (
    are_concat_streams_compatible,
    build_concat_compatibility_report,
)

REVIEW_ACTION_HANDLERS = build_review_action_handlers()


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


def ask_concat_count(default_value: str) -> str:
    return require_non_empty(
        ask_text(
            "何本の動画を結合しますか？\n2以上の整数を入力してください",
            default=default_value,
        ),
        "結合本数",
    )


def ask_concat_file(index: int, default_value: str | None) -> str:
    return require_non_empty(
        ask_text(
            f"結合する動画ファイル {index + 1} を入力してください\n例: ./videos/part{index + 1}.mp4",
            default=default_value,
        ),
        f"入力ファイル{index + 1}",
    )


def ask_concat_output(default_value: str) -> str:
    return require_non_empty(
        ask_text(
            "出力ファイル名を入力してください\n例: ./output/merged.mp4",
            default=default_value,
        ),
        "出力ファイル",
    )


def collect_concat_files(form: ConcatForm, count: int) -> list[str]:
    input_files: list[str] = []
    for index in range(count):
        default_value = form.input_files[index] if index < len(form.input_files) else None
        file_path = ask_concat_file(index, default_value)
        validate_input_file_exists(file_path)
        validate_video_file_extension(file_path)
        input_files.append(file_path)
    return input_files


def collect_concat_input(form: ConcatForm):
    count_raw = ask_concat_count(form.count_raw)
    count = parse_concat_count(count_raw)
    input_files = collect_concat_files(form, count)

    output_file = ask_concat_output(form.output_file)
    validate_output_directory_exists(output_file)

    media_infos = [probe_media_info(path) for path in input_files]
    compatible = are_concat_streams_compatible(media_infos)

    return replace(
        form,
        count_raw=count_raw,
        input_files=input_files,
        output_file=output_file,
    ), media_infos, compatible


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


def edit_concat_form(form: ConcatForm) -> ConcatForm:
    fields = [("結合本数", "count_raw")]
    fields.extend((f"入力ファイル{i + 1}", f"input_{i}") for i in range(max(1, len(form.input_files))))
    fields.append(("出力ファイル", "output_file"))

    field = ask_field_to_edit(fields)

    if field == "count_raw":
        value = require_non_empty(ask_text("結合本数を再入力してください", default=form.count_raw), "結合本数")
        return replace(form, count_raw=value)

    if field == "output_file":
        value = require_non_empty(ask_text("出力ファイルを再入力してください", default=form.output_file), "出力ファイル")
        return replace(form, output_file=value)

    index = int(field.split("_")[1])
    default_value = form.input_files[index] if index < len(form.input_files) else None
    value = require_non_empty(
        ask_text(f"入力ファイル{index + 1}を再入力してください", default=default_value),
        f"入力ファイル{index + 1}",
    )
    return replace(form, input_files=update_concat_file(form.input_files, index, value))



def handle_concat_review(form: ConcatForm) -> FlowResult:
    action = ask_review_action()
    flow_action, updated_form = REVIEW_ACTION_HANDLERS[action](
        form,
        {
            "empty_form_factory": ConcatForm,
            "edit_form": edit_concat_form,
        },
    )
    return FLOW_RESULT_FACTORIES[flow_action](updated_form)


def build_concat_command(
    form: ConcatForm,
    compatible: bool,
    concat_list_file: str,
) -> list[str]:
    strategy = choose_concat_strategy(compatible)
    return strategy.build(concat_list_file, form.output_file)


def print_concat_command(command: list[str]) -> None:
    print("生成された FFmpeg コマンド:")
    print(format_command(command))
    print()


def print_concat_execution_result(output_file: str, executed: bool) -> None:
    if executed:
        print(f"完了: {output_file}")
        return
    print("ドライラン完了: 実行はしていません。")


def execute_concat(form: ConcatForm, compatible: bool, dry_run: bool = False) -> None:
    concat_list_file = create_concat_list_file(form.input_files)

    try:
        command = build_concat_command(form, compatible, concat_list_file)
        print_concat_command(command)
        result = run_ffmpeg(command, dry_run=dry_run)
        print_concat_execution_result(form.output_file, result.executed)
    finally:
        path = Path(concat_list_file)
        path.unlink(missing_ok=True)


def should_return_immediately(result: FlowResult) -> bool:
    return result.kind in {"retry", "done"}


def execute_reviewed_concat(review_result: FlowResult, compatible: bool) -> FlowResult:
    if review_result.kind == "dry_run":
        execute_concat(review_result.form, compatible, dry_run=True)
        return FlowResult(kind="done", form=review_result.form)

    execute_concat(review_result.form, compatible, dry_run=False)
    return FlowResult(kind="done", form=review_result.form)


def run_concat_iteration(form: ConcatForm) -> FlowResult:
    try:
        updated_form, media_infos, compatible = collect_concat_input(form)
        summary = build_concat_summary(updated_form, media_infos, compatible)
        print("\n" + summary + "\n")

        review_result = handle_concat_review(updated_form)
        if should_return_immediately(review_result):
            return review_result

        return execute_reviewed_concat(review_result, compatible)

    except ValidationError as exc:
        print(f"\n入力エラー: {exc}")
        return FlowResult(kind="retry", form=form)


def run_concat_flow() -> None:
    form = ConcatForm()

    while True:
        result = run_concat_iteration(form)
        if result.kind == "done":
            return
        form = result.form
