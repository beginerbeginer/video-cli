import unittest
from unittest.mock import patch

from domain import operations
from ui.cli.main_menu import prompt_main_menu

CURRENT_MENU_CHOICES = [
    ("動画を切り出す", operations.TRIM),
    ("動画を結合する", operations.CONCAT),
    ("動画サイズを変更する", operations.RESIZE),
    ("音量を調整する", operations.VOLUME),
    ("音声を抽出する", operations.AUDIO_EXTRACT),
    ("サムネイルを抽出する", operations.THUMBNAIL),
    ("GIFに変換する", operations.GIF),
    ("速度を変更する", operations.SPEED),
    ("音声を削除する", operations.MUTE),
    ("フォーマットを変換する", operations.CONVERT),
    ("回転・反転する", operations.ROTATE),
    ("動画情報を確認する", operations.INFO),
    ("動画をクロップする", operations.CROP),
    ("動画を圧縮する", operations.COMPRESS),
    ("フレームレートを変換する", operations.FPS),
    ("終了する", operations.EXIT),
]


class TestPromptMainMenu(unittest.TestCase):
    def test_メニューは従来と同じ順番と文言で表示される(self):
        # Arrange
        with patch("ui.cli.main_menu.ask_menu", return_value=operations.TRIM) as ask_menu:
            # Act
            result = prompt_main_menu()

        # Assert
        self.assertEqual(result, operations.TRIM)
        ask_menu.assert_called_once_with("何をしたいですか？", CURRENT_MENU_CHOICES)


class TestOperationLabels(unittest.TestCase):
    def test_表示名はメニューと同じ順番で全操作分そろっている(self):
        # Arrange
        expected = [(operation, label) for label, operation in CURRENT_MENU_CHOICES]

        # Act
        actual = list(operations.OPERATION_LABELS.items())

        # Assert
        self.assertEqual(actual, expected)
