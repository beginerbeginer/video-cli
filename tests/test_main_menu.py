import unittest
from unittest.mock import patch

from domain import operations
from ui.cli.main_menu import prompt_main_menu


class TestPromptMainMenu(unittest.TestCase):
    def test_menu_keeps_current_order_and_labels(self):
        with patch("ui.cli.main_menu.ask_menu", return_value=operations.TRIM) as ask_menu:
            result = prompt_main_menu()

        self.assertEqual(result, operations.TRIM)
        ask_menu.assert_called_once_with(
            "何をしたいですか？",
            [
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
            ],
        )


class TestOperationLabels(unittest.TestCase):
    def test_every_operation_has_label(self):
        self.assertEqual(operations.OPERATION_LABELS[operations.TRIM], "動画を切り出す")
        self.assertEqual(operations.OPERATION_LABELS[operations.EXIT], "終了する")
        self.assertEqual(len(operations.OPERATION_LABELS), 16)
