import unittest

from shared.command_formatter import format_command


class TestFormatCommand(unittest.TestCase):
    def test_basic_join(self):
        command = ["ffmpeg", "-i", "in.mp4", "out.mp4"]
        result = format_command(command)

        self.assertEqual(result, "ffmpeg -i in.mp4 out.mp4")

    def test_empty(self):
        self.assertEqual(format_command([]), "")


if __name__ == "__main__":
    unittest.main()
