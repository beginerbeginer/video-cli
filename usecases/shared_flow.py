from typing import Any, Callable

from shared.errors import ValidationError
from ui.review import ask_review_action
from ui.review_actions import build_review_action_handlers
from usecases.flow_result import FLOW_RESULT_FACTORIES, FlowResult

_REVIEW_ACTION_HANDLERS = build_review_action_handlers()


def handle_generic_review(
    form: Any,
    empty_form_factory: Callable,
    edit_form_fn: Callable,
) -> FlowResult:
    action = ask_review_action()
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
) -> FlowResult:
    try:
        updated_form, *extra = collect_fn(form)
        summary = build_summary_fn(updated_form, *extra)
        print("\n" + summary + "\n")

        review_result = handle_generic_review(updated_form, empty_form_factory, edit_form_fn)

        if review_result.kind in {"retry", "done"}:
            return review_result

        execute_fn(review_result.form, dry_run=(review_result.kind == "dry_run"))
        return FlowResult(kind="done", form=review_result.form)

    except ValidationError as exc:
        print(f"\n入力エラー: {exc}")
        return FlowResult(kind="retry", form=form)


def run_flow(form: Any, iterate_fn: Callable) -> None:
    while True:
        result = iterate_fn(form)
        if result.kind == "done":
            return
        form = result.form
