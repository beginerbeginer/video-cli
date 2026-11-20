import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from api.paths import ROOT_ENV, PathOutsideRootError, get_allowed_root, is_within_root, resolve_within_root


class TestGetAllowedRoot(unittest.TestCase):
    def test_環境変数が無いとホームディレクトリになる(self):
        # Arrange
        env = {k: v for k, v in os.environ.items() if k != ROOT_ENV}

        # Act
        with patch.dict(os.environ, env, clear=True):
            root = get_allowed_root()

        # Assert
        self.assertEqual(root, Path.home().resolve())

    def test_VIDEO_GUI_ROOTを指定するとそのディレクトリになる(self):
        # Arrange
        with tempfile.TemporaryDirectory() as tmp:
            # Act
            with patch.dict(os.environ, {ROOT_ENV: tmp}):
                root = get_allowed_root()

            # Assert
            self.assertEqual(root, Path(tmp).resolve())


class TestIsWithinRoot(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        base = Path(self._tmp.name).resolve()
        self.root = base / "root"
        self.outside = base / "outside"
        self.root.mkdir()
        self.outside.mkdir()
        (self.root / "in.mp4").touch()
        (self.outside / "secret.mp4").touch()

    def tearDown(self):
        self._tmp.cleanup()

    def test_範囲内のファイルは許可される(self):
        # Act / Assert
        self.assertTrue(is_within_root(self.root / "in.mp4", self.root))

    def test_ルートそのものは許可される(self):
        # Act / Assert
        self.assertTrue(is_within_root(self.root, self.root))

    def test_まだ無い範囲内のパスは許可される(self):
        # Act / Assert
        self.assertTrue(is_within_root(self.root / "out" / "new.mp4", self.root))

    def test_範囲外のパスは拒否される(self):
        # Act / Assert
        self.assertFalse(is_within_root(self.outside / "secret.mp4", self.root))

    def test_dotdotで範囲外に出るパスは拒否される(self):
        # Arrange
        path = self.root / ".." / "outside" / "secret.mp4"

        # Act / Assert
        self.assertFalse(is_within_root(path, self.root))

    def test_名前がルートで始まるだけの別ディレクトリは拒否される(self):
        # Arrange
        sibling = self.root.parent / "root-evil"
        sibling.mkdir()

        # Act / Assert
        self.assertFalse(is_within_root(sibling / "x.mp4", self.root))

    def test_範囲外を指すシンボリックリンクは拒否される(self):
        # Arrange
        link = self.root / "link.mp4"
        link.symlink_to(self.outside / "secret.mp4")

        # Act / Assert
        self.assertFalse(is_within_root(link, self.root))

    def test_範囲外のディレクトリを指すシンボリックリンクの下も拒否される(self):
        # Arrange
        link_dir = self.root / "linkdir"
        link_dir.symlink_to(self.outside, target_is_directory=True)

        # Act / Assert
        self.assertFalse(is_within_root(link_dir / "secret.mp4", self.root))

    def test_ルートがシンボリックリンクでも実体の中なら許可される(self):
        # Arrange
        root_link = self.root.parent / "root-link"
        root_link.symlink_to(self.root, target_is_directory=True)

        # Act / Assert
        self.assertTrue(is_within_root(self.root / "in.mp4", root_link))


class TestResolveWithinRoot(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        base = Path(self._tmp.name).resolve()
        self.root = base / "root"
        self.outside = base / "outside"
        self.root.mkdir()
        self.outside.mkdir()
        (self.root / "in.mp4").touch()
        (self.outside / "secret.mp4").touch()

    def tearDown(self):
        self._tmp.cleanup()

    def test_範囲内のパスは解決済みの絶対パスで返る(self):
        # Arrange
        path = self.root / "sub" / ".." / "in.mp4"

        # Act
        resolved = resolve_within_root(path, self.root)

        # Assert
        self.assertEqual(resolved, self.root / "in.mp4")

    def test_範囲内を指すシンボリックリンクは実体のパスで返る(self):
        # Arrange
        link = self.root / "link.mp4"
        link.symlink_to(self.root / "in.mp4")

        # Act
        resolved = resolve_within_root(link, self.root)

        # Assert
        self.assertEqual(resolved, self.root / "in.mp4")

    def test_範囲外のパスはPathOutsideRootErrorになる(self):
        # Act / Assert
        with self.assertRaises(PathOutsideRootError):
            resolve_within_root(self.outside / "secret.mp4", self.root)

    def test_dotdotで範囲外に出るパスはPathOutsideRootErrorになる(self):
        # Act / Assert
        with self.assertRaises(PathOutsideRootError):
            resolve_within_root(self.root / ".." / "outside" / "secret.mp4", self.root)

    def test_範囲外を指すシンボリックリンクはPathOutsideRootErrorになる(self):
        # Arrange
        link = self.root / "link.mp4"
        link.symlink_to(self.outside / "secret.mp4")

        # Act / Assert
        with self.assertRaises(PathOutsideRootError):
            resolve_within_root(link, self.root)

    def test_エラーのメッセージに範囲外のパスを含めない(self):
        # Act
        with self.assertRaises(PathOutsideRootError) as ctx:
            resolve_within_root(self.outside / "secret.mp4", self.root)

        # Assert
        self.assertNotIn("outside", str(ctx.exception))
