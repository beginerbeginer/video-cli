import unittest
from collections.abc import Sequence
from unittest.mock import Mock

from main import build_operation_handlers, dispatch_operation
from usecases.ui_port import UIPort


class TestDispatchOperation(unittest.TestCase):
    def test_dispatch_known_operation(self):
        trim_handler = Mock()
        unknown_handler = Mock()

        handlers = {
            "trim": trim_handler,
        }

        dispatch_operation(
            operation="trim",
            handlers=handlers,
            unknown_handler=unknown_handler,
        )

        trim_handler.assert_called_once_with()
        unknown_handler.assert_not_called()

    def test_dispatch_unknown_operation(self):
        trim_handler = Mock()
        unknown_handler = Mock()

        handlers = {
            "trim": trim_handler,
        }

        dispatch_operation(
            operation="unknown",
            handlers=handlers,
            unknown_handler=unknown_handler,
        )

        trim_handler.assert_not_called()
        unknown_handler.assert_called_once_with()


class TestBuildOperationHandlers(unittest.TestCase):
    def test_accepts_any_ui_port_implementation(self):
        # CliUI ではなく UIPort を満たす任意の実装を渡せることを確認する
        class StubUI:
            def ask_text(self, message: str, default: str | None = None) -> str:
                return default or ""

            def ask_menu(self, message: str, choices: Sequence[tuple[str, str]]) -> str:
                return choices[0][1] if choices else ""

        stub = StubUI()
        # CliUI 固有の型しか受け入れない実装だと、ここで TypeError が上がる
        handlers = build_operation_handlers(stub)
        self.assertIn("trim", handlers)
        self.assertIn("fps", handlers)


if __name__ == "__main__":
    unittest.main()
