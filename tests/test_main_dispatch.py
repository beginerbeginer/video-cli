import unittest
from unittest.mock import Mock

from main import dispatch_operation


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


if __name__ == "__main__":
    unittest.main()
