from dataclasses import dataclass
from typing import Literal

FlowKind = Literal["done", "retry", "dry_run", "execute"]


@dataclass(frozen=True)
class FlowResult:
    kind: FlowKind
    form: object


def _to_done(form) -> "FlowResult":
    return FlowResult(kind="done", form=form)


def _to_retry(form) -> "FlowResult":
    return FlowResult(kind="retry", form=form)


def _to_dry_run(form) -> "FlowResult":
    return FlowResult(kind="dry_run", form=form)


def _to_execute(form) -> "FlowResult":
    return FlowResult(kind="execute", form=form)


FLOW_RESULT_FACTORIES = {
    "return": _to_done,
    "continue": _to_retry,
    "dry_run": _to_dry_run,
    "execute": _to_execute,
}
