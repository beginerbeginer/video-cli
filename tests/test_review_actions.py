import unittest
from dataclasses import dataclass

from ui.review_actions import (
    cancel_action,
    dry_run_action,
    edit_action,
    execute_action,
    restart_action,
)


@dataclass
class DummyForm:
    value: str = "old"


class TestReviewActions(unittest.TestCase):
    def test_cancel_action(self):
        form = DummyForm()

        kind, updated = cancel_action(form, {})

        self.assertEqual(kind, "return")
        self.assertEqual(updated, form)

    def test_execute_action(self):
        form = DummyForm()

        kind, updated = execute_action(form, {})

        self.assertEqual(kind, "execute")
        self.assertEqual(updated, form)

    def test_dry_run_action(self):
        form = DummyForm()

        kind, updated = dry_run_action(form, {})

        self.assertEqual(kind, "dry_run")
        self.assertEqual(updated, form)

    def test_restart_action(self):
        form = DummyForm()

        def empty_factory():
            return DummyForm(value="new")

        kind, updated = restart_action(
            form,
            {"empty_form_factory": empty_factory},
        )

        self.assertEqual(kind, "continue")
        self.assertEqual(updated, DummyForm(value="new"))

    def test_edit_action(self):
        form = DummyForm()

        def edit_form(current):
            return DummyForm(value=current.value + "-edited")

        kind, updated = edit_action(
            form,
            {"edit_form": edit_form},
        )

        self.assertEqual(kind, "continue")
        self.assertEqual(updated, DummyForm(value="old-edited"))


if __name__ == "__main__":
    unittest.main()
