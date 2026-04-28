import unittest

from ffmpeg.concat_strategy import (
    CopyConcatStrategy,
    ReencodeConcatStrategy,
    choose_concat_strategy,
)


class TestConcatStrategy(unittest.TestCase):
    def test_choose_copy_strategy_when_compatible(self):
        strategy = choose_concat_strategy(True)
        self.assertIsInstance(strategy, CopyConcatStrategy)

    def test_choose_reencode_strategy_when_incompatible(self):
        strategy = choose_concat_strategy(False)
        self.assertIsInstance(strategy, ReencodeConcatStrategy)

    def test_copy_strategy_builds_copy_command(self):
        strategy = CopyConcatStrategy()
        command = strategy.build("list.txt", "out.mp4")

        self.assertEqual(
            command,
            [
                "ffmpeg",
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                "list.txt",
                "-c",
                "copy",
                "out.mp4",
            ],
        )

    def test_reencode_strategy_builds_reencode_command(self):
        strategy = ReencodeConcatStrategy()
        command = strategy.build("list.txt", "out.mp4")

        self.assertEqual(
            command,
            [
                "ffmpeg",
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                "list.txt",
                "-c:v",
                "libx264",
                "-c:a",
                "aac",
                "out.mp4",
            ],
        )


if __name__ == "__main__":
    unittest.main()
