from collections.abc import Callable
from typing import Any

ReviewContext = dict[str, Any]
ReviewResult = tuple[str, object]


def cancel_action(form: object, context: ReviewContext) -> ReviewResult:
    print("処理を中止しました。")
    return "return", form


def restart_action(form: object, context: ReviewContext) -> ReviewResult:
    empty_form_factory: Callable[[], object] = context["empty_form_factory"]
    return "continue", empty_form_factory()


def edit_action(form: object, context: ReviewContext) -> ReviewResult:
    edit_form: Callable[[object], object] = context["edit_form"]
    return "continue", edit_form(form)


def execute_action(form: object, context: ReviewContext) -> ReviewResult:
    return "execute", form


def dry_run_action(form: object, context: ReviewContext) -> ReviewResult:
    return "dry_run", form


def build_review_action_handlers() -> dict[str, Callable[[object, ReviewContext], ReviewResult]]:
    return {
        "cancel": cancel_action,
        "restart": restart_action,
        "edit": edit_action,
        "execute": execute_action,
        "dry_run": dry_run_action,
    }
