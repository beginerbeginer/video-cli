import unittest
from pathlib import Path

TEST_WORKFLOW = Path(__file__).resolve().parent.parent / ".github" / "workflows" / "test.yml"


class TestTestWorkflowSteps(unittest.TestCase):
    """CI で確かめる品質チェックが抜け落ちないことを固定する。"""

    def setUp(self):
        self.text = TEST_WORKFLOW.read_text(encoding="utf-8")

    def test_lintを確かめる(self):
        self.assertIn("uv run ruff check .", self.text)

    def test_formatを確かめる(self):
        # Why not `ruff format .`: CI で書き換えても main には反映されず、整っていないことに気づけない
        self.assertIn("uv run ruff format --check .", self.text)

    def test_テストを実行する(self):
        self.assertIn("uv run pytest", self.text)


if __name__ == "__main__":
    unittest.main()
