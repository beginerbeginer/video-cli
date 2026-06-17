import sys
from collections.abc import Callable
from typing import Any

from ffmpeg.runner import ProgressInfo, run_ffmpeg
from shared.command_formatter import format_command
from shared.errors import ValidationError
from usecases.flow_result import FLOW_RESULT_FACTORIES, FlowResult
from usecases.review_actions import build_review_action_handlers
from usecases.ui_port import UIPort

_REVIEW_ACTION_HANDLERS = build_review_action_handlers()

_REVIEW_CHOICES = [
    ("この内容で実行する", "execute"),
    ("ドライランする（実行しない）", "dry_run"),
    ("最初からやり直す", "restart"),
    ("特定項目を修正する", "edit"),
    ("中止する", "cancel"),
]


def make_cli_progress_callback() -> Callable[[ProgressInfo], None]:
    # print ではなく sys.stdout.write + flush を使う。
    # print は改行を付加するため \r による行上書きができないため。
    def callback(info: ProgressInfo) -> None:
        sys.stdout.write(f"\r経過時間: {info.out_time}  速度: {info.speed}    ")
        sys.stdout.flush()

    return callback


def execute_with_output(command: list[str], output_file: str, dry_run: bool) -> None:
    print("生成された FFmpeg コマンド:")
    print(format_command(command))
    print()

    result = run_ffmpeg(command, dry_run=dry_run, progress_callback=make_cli_progress_callback())

    if result.executed:
        # プログレスバーの \r 行の後に改行してから完了メッセージを出す
        print()
        print(f"完了: {output_file}")
    else:
        print("ドライラン完了: 実行はしていません。")


def handle_generic_review(
    form: Any,
    empty_form_factory: Callable,
    edit_form_fn: Callable,
    ui: UIPort,
) -> FlowResult:
    action = ui.ask_menu("次にどうしますか？", _REVIEW_CHOICES)
    flow_action, updated_form = _REVIEW_ACTION_HANDLERS[action](
        form,
        {
            "empty_form_factory": empty_form_factory,
            "edit_form": edit_form_fn,
        },
    )
    return FLOW_RESULT_FACTORIES[flow_action](updated_form)


def run_generic_iteration(
    form: Any,
    collect_fn: Callable,
    build_summary_fn: Callable,
    empty_form_factory: Callable,
    edit_form_fn: Callable,
    execute_fn: Callable,
    ui: UIPort,
) -> FlowResult:
    try:
        updated_form, *extra = collect_fn(form, ui)
        summary = build_summary_fn(updated_form, *extra)
        print("\n" + summary + "\n")

        review_result = handle_generic_review(
            updated_form,
            empty_form_factory,
            lambda f: edit_form_fn(f, ui),
            ui,
        )

        if review_result.kind in {"retry", "done"}:
            return review_result

        execute_fn(review_result.form, dry_run=(review_result.kind == "dry_run"))
        return FlowResult(kind="done", form=review_result.form)

    except ValidationError as exc:
        print(f"\n入力エラー: {exc}")
        return FlowResult(kind="retry", form=form)


def run_flow(form: Any, iterate_fn: Callable, ui: UIPort) -> None:
    while True:
        result = iterate_fn(form, ui)
        if result.kind == "done":
            return
        form = result.form
