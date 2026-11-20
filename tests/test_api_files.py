import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from api.app import create_app
from api.paths import ROOT_ENV

FFPROBE_OUTPUT = {
    "format": {"format_name": "mov,mp4,m4a,3gp,3g2,mj2", "duration": "12.5"},
    "streams": [
        {"codec_type": "video", "codec_name": "h264", "width": 1920, "height": 1080, "avg_frame_rate": "30/1"},
        {"codec_type": "audio", "codec_name": "aac"},
    ],
}


class _ApiWithRootTestCase(unittest.TestCase):
    """一時ディレクトリの root/ を参照範囲にし、その隣に範囲外の outside/ を置く。"""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        base = Path(self._tmp.name).resolve()
        self.root = base / "root"
        self.outside = base / "outside"
        self.root.mkdir()
        self.outside.mkdir()
        (self.outside / "secret.mp4").write_bytes(b"secret")

        env = patch.dict(os.environ, {ROOT_ENV: str(self.root)})
        env.start()
        self.addCleanup(env.stop)
        # Why not TestClient の既定（Host: testserver）: Host の確認で拒否されるため、実際の起動先にそろえる。
        self.client = TestClient(create_app(), base_url="http://127.0.0.1:8000")

    def tearDown(self):
        self._tmp.cleanup()

    def assert_forbidden_without_leaking(self, res):
        self.assertEqual(res.status_code, 403)
        self.assertNotIn("outside", res.text)
        self.assertNotIn("secret", res.text)


class TestFsHome(_ApiWithRootTestCase):
    def test_ホームが参照範囲の外なら参照範囲のルートが返る(self):
        # Arrange
        with patch("api.files.Path.home", return_value=self.outside):
            # Act
            res = self.client.get("/api/fs/home")

        # Assert
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json(), {"path": str(self.root)})

    def test_ホームが参照範囲の中ならホームが返る(self):
        # Arrange
        home = self.root / "me"
        home.mkdir()
        with patch("api.files.Path.home", return_value=home):
            # Act
            res = self.client.get("/api/fs/home")

        # Assert
        self.assertEqual(res.json(), {"path": str(home)})


class TestFsList(_ApiWithRootTestCase):
    def _list(self, path):
        return self.client.get("/api/fs/list", params={"path": str(path)})

    def _names(self, res) -> list[str]:
        return [entry["name"] for entry in res.json()["entries"]]

    def test_ディレクトリの中身がディレクトリ優先の名前順で返る(self):
        # Arrange
        (self.root / "b.mp4").write_bytes(b"12345")
        (self.root / "A.txt").touch()
        (self.root / "videos").mkdir()

        # Act
        res = self._list(self.root)

        # Assert
        self.assertEqual(res.status_code, 200)
        self.assertEqual(self._names(res), ["videos", "A.txt", "b.mp4"])

    def test_各項目にパスと種類とサイズと更新日時と動画かどうかが入る(self):
        # Arrange
        video = self.root / "b.MP4"
        video.write_bytes(b"12345")
        (self.root / "videos").mkdir()

        # Act
        entries = {e["name"]: e for e in self._list(self.root).json()["entries"]}

        # Assert
        self.assertEqual(entries["b.MP4"]["path"], str(video))
        self.assertEqual(entries["b.MP4"]["kind"], "file")
        self.assertEqual(entries["b.MP4"]["size"], 5)
        self.assertTrue(entries["b.MP4"]["is_video"])
        self.assertIsInstance(entries["b.MP4"]["modified"], str)
        self.assertEqual(entries["videos"]["kind"], "dir")
        self.assertIsNone(entries["videos"]["size"])
        self.assertFalse(entries["videos"]["is_video"])

    def test_動画の拡張子でないファイルはis_videoがfalseになる(self):
        # Arrange
        (self.root / "memo.txt").touch()

        # Act
        entry = self._list(self.root).json()["entries"][0]

        # Assert
        self.assertFalse(entry["is_video"])

    def test_隠しファイルと隠しディレクトリは除かれる(self):
        # Arrange
        (self.root / ".hidden.mp4").touch()
        (self.root / ".cache").mkdir()
        (self.root / "shown.mp4").touch()

        # Act
        res = self._list(self.root)

        # Assert
        self.assertEqual(self._names(res), ["shown.mp4"])

    def test_シンボリックリンクは範囲内を指していても除かれる(self):
        # Arrange
        (self.root / "real.mp4").touch()
        (self.root / "link.mp4").symlink_to(self.root / "real.mp4")
        (self.root / "linkdir").symlink_to(self.outside, target_is_directory=True)

        # Act
        res = self._list(self.root)

        # Assert
        self.assertEqual(self._names(res), ["real.mp4"])

    def test_サブディレクトリでは親のパスが返る(self):
        # Arrange
        sub = self.root / "videos"
        sub.mkdir()

        # Act
        body = self._list(sub).json()

        # Assert
        self.assertEqual(body["path"], str(sub))
        self.assertEqual(body["parent"], str(self.root))

    def test_ルートでは親がnullになる(self):
        # Act
        body = self._list(self.root).json()

        # Assert
        self.assertEqual(body["path"], str(self.root))
        self.assertIsNone(body["parent"])

    def test_pathを省略すると参照範囲のルートが返る(self):
        # Act
        res = self.client.get("/api/fs/list")

        # Assert
        self.assertEqual(res.json()["path"], str(self.root))

    def test_dotdotを含むが範囲内に収まるパスは解決済みのパスで返る(self):
        # Arrange
        (self.root / "videos").mkdir()

        # Act
        body = self._list(f"{self.root}/videos/..").json()

        # Assert
        self.assertEqual(body["path"], str(self.root))

    def test_範囲外のパスは403になり中身を返さない(self):
        # Act
        res = self._list(self.outside)

        # Assert
        self.assert_forbidden_without_leaking(res)

    def test_dotdotで範囲外に出るパスは403になる(self):
        # Act
        res = self._list(f"{self.root}/../outside")

        # Assert
        self.assert_forbidden_without_leaking(res)

    def test_範囲外を指すシンボリックリンクは403になる(self):
        # Arrange
        link = self.root / "linkdir"
        link.symlink_to(self.outside, target_is_directory=True)

        # Act
        res = self._list(link)

        # Assert
        self.assert_forbidden_without_leaking(res)

    def test_403はerrorsの形式で返る(self):
        # Act
        res = self._list(self.outside)

        # Assert
        self.assertEqual(res.json(), {"errors": [{"field": "path", "message": "参照できる範囲の外のパスです。"}]})

    def test_存在しないディレクトリは422になる(self):
        # Act
        res = self._list(self.root / "missing")

        # Assert
        self.assertEqual(res.status_code, 422)
        self.assertEqual(res.json()["errors"][0]["field"], "path")

    def test_ファイルを指定すると422になる(self):
        # Arrange
        (self.root / "in.mp4").touch()

        # Act
        res = self._list(self.root / "in.mp4")

        # Assert
        self.assertEqual(res.status_code, 422)
        self.assertEqual(res.json()["errors"][0]["field"], "path")

    def test_相対パスは422になる(self):
        # Act
        res = self._list("videos")

        # Assert
        self.assertEqual(res.status_code, 422)
        self.assertEqual(res.json()["errors"][0]["field"], "path")


class TestProbe(_ApiWithRootTestCase):
    def setUp(self):
        super().setUp()
        self.video = self.root / "in.mp4"
        self.video.write_bytes(b"video")
        which = patch("ffmpeg.probe.shutil.which", return_value="/usr/bin/ffprobe")
        which.start()
        self.addCleanup(which.stop)

    def _probe(self, path):
        return self.client.post("/api/probe", json={"path": str(path)})

    def test_範囲内の動画はMediaInfoのJSONが返る(self):
        # Arrange
        with patch("ffmpeg.probe.run_ffprobe", return_value=FFPROBE_OUTPUT) as run_ffprobe:
            # Act
            res = self._probe(self.video)

        # Assert
        self.assertEqual(res.status_code, 200)
        self.assertEqual(
            res.json(),
            {
                "path": str(self.video),
                "duration_seconds": 12.5,
                "format_name": "mov,mp4,m4a,3gp,3g2,mj2",
                "video": {"codec_name": "h264", "width": 1920, "height": 1080, "fps": 30.0},
                "audio": {"codec_name": "aac"},
            },
        )
        run_ffprobe.assert_called_once_with(str(self.video))

    def test_音声の無い動画はaudioがnullで返る(self):
        # Arrange
        output = {**FFPROBE_OUTPUT, "streams": FFPROBE_OUTPUT["streams"][:1]}
        with patch("ffmpeg.probe.run_ffprobe", return_value=output):
            # Act
            res = self._probe(self.video)

        # Assert
        self.assertIsNone(res.json()["audio"])

    def test_範囲外のパスは403になりffprobeを呼ばない(self):
        # Arrange
        with patch("ffmpeg.probe.run_ffprobe") as run_ffprobe:
            # Act
            res = self._probe(self.outside / "secret.mp4")

        # Assert
        self.assert_forbidden_without_leaking(res)
        run_ffprobe.assert_not_called()

    def test_dotdotで範囲外に出るパスは403になる(self):
        # Arrange
        with patch("ffmpeg.probe.run_ffprobe") as run_ffprobe:
            # Act
            res = self._probe(f"{self.root}/../outside/secret.mp4")

        # Assert
        self.assert_forbidden_without_leaking(res)
        run_ffprobe.assert_not_called()

    def test_範囲外を指すシンボリックリンクは403になる(self):
        # Arrange
        link = self.root / "link.mp4"
        link.symlink_to(self.outside / "secret.mp4")
        with patch("ffmpeg.probe.run_ffprobe") as run_ffprobe:
            # Act
            res = self._probe(link)

        # Assert
        self.assert_forbidden_without_leaking(res)
        run_ffprobe.assert_not_called()

    def test_範囲外の存在しないパスも403になり存在を教えない(self):
        # Act
        res = self._probe(self.outside / "missing.mp4")

        # Assert
        self.assert_forbidden_without_leaking(res)

    def test_範囲内を指すシンボリックリンクは既存のvalidatorと同じく422になる(self):
        # Arrange
        link = self.root / "link.mp4"
        link.symlink_to(self.video)
        with patch("ffmpeg.probe.run_ffprobe") as run_ffprobe:
            # Act
            res = self._probe(link)

        # Assert
        self.assertEqual(res.status_code, 422)
        self.assertEqual(res.json()["errors"][0]["field"], "path")
        run_ffprobe.assert_not_called()

    def test_存在しないファイルは422とerrorsで返る(self):
        # Act
        res = self._probe(self.root / "missing.mp4")

        # Assert
        self.assertEqual(res.status_code, 422)
        self.assertEqual(
            res.json(),
            {"errors": [{"field": "path", "message": f"入力ファイルが見つかりません: {self.root / 'missing.mp4'}"}]},
        )

    def test_ディレクトリを指定すると422になる(self):
        # Act
        res = self._probe(self.root)

        # Assert
        self.assertEqual(res.status_code, 422)
        self.assertEqual(res.json()["errors"][0]["field"], "path")

    def test_相対パスは422になる(self):
        # Act
        res = self.client.post("/api/probe", json={"path": "in.mp4"})

        # Assert
        self.assertEqual(res.status_code, 422)
        self.assertEqual(res.json()["errors"][0]["field"], "path")

    def test_ffprobeが失敗すると422とerrorsで返る(self):
        # Arrange
        from shared.errors import ValidationError

        error = ValidationError(f"ffprobe でメディア情報を取得できませんでした: {self.video}")
        with patch("ffmpeg.probe.run_ffprobe", side_effect=error):
            # Act
            res = self._probe(self.video)

        # Assert
        self.assertEqual(res.status_code, 422)
        self.assertEqual(res.json()["errors"][0]["field"], "path")

    def test_ffprobeが無いと422でfieldがnullになる(self):
        # Arrange
        with patch("ffmpeg.probe.shutil.which", return_value=None):
            # Act
            res = self._probe(self.video)

        # Assert
        self.assertEqual(res.status_code, 422)
        self.assertIsNone(res.json()["errors"][0]["field"])

    def test_JSON以外の本文は415で拒否される(self):
        # Act
        res = self.client.post("/api/probe", data={"path": str(self.video)})

        # Assert
        self.assertEqual(res.status_code, 415)


class TestDocs(_ApiWithRootTestCase):
    def test_ファイル参照とprobeのAPIがOpenAPIに載る(self):
        # Act
        paths = self.client.get("/openapi.json").json()["paths"]

        # Assert
        self.assertIn("get", paths["/api/fs/home"])
        self.assertIn("get", paths["/api/fs/list"])
        self.assertIn("post", paths["/api/probe"])
