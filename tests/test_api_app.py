import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from api.app import create_app
from domain import operations
from shared.errors import ValidationError


def _local_client(app=None) -> TestClient:
    # Why not TestClient の既定（Host: testserver）: Host の確認で拒否されるため、実際の起動先にそろえる。
    return TestClient(app or create_app(), base_url="http://127.0.0.1:8000")


def _which_only(*available: str):
    return lambda name: f"/usr/bin/{name}" if name in available else None


class TestHealth(unittest.TestCase):
    def setUp(self):
        self.client = _local_client()

    def test_ffmpegとffprobeがあると両方trueが返る(self):
        # Arrange
        with patch("ffmpeg.probe.shutil.which", side_effect=_which_only("ffmpeg", "ffprobe")):
            # Act
            res = self.client.get("/api/health")

        # Assert
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json(), {"ffmpeg": True, "ffprobe": True})

    def test_ffprobeが無いとffprobeだけfalseが返る(self):
        # Arrange
        with patch("ffmpeg.probe.shutil.which", side_effect=_which_only("ffmpeg")):
            # Act
            res = self.client.get("/api/health")

        # Assert
        self.assertEqual(res.json(), {"ffmpeg": True, "ffprobe": False})


class TestOperations(unittest.TestCase):
    def test_操作一覧はメニュー順でexitを除いて返る(self):
        # Arrange
        client = _local_client()
        expected = [
            {"id": operation, "label": label}
            for operation, label in operations.OPERATION_LABELS.items()
            if operation != operations.EXIT
        ]

        # Act
        res = client.get("/api/operations")

        # Assert
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json(), expected)
        self.assertEqual(res.json()[0], {"id": operations.TRIM, "label": "動画を切り出す"})


class TestValidationErrorHandler(unittest.TestCase):
    def _client_raising(self, exc: Exception) -> TestClient:
        app = create_app()

        @app.get("/api/_raise")
        def _raise():
            raise exc

        return _local_client(app)

    def test_fieldつきのValidationErrorは422とerrorsで返る(self):
        # Arrange
        exc = ValidationError("開始時刻の形式が正しくありません。")
        exc.field = "start_raw"
        client = self._client_raising(exc)

        # Act
        res = client.get("/api/_raise")

        # Assert
        self.assertEqual(res.status_code, 422)
        self.assertEqual(
            res.json(),
            {"errors": [{"field": "start_raw", "message": "開始時刻の形式が正しくありません。"}]},
        )

    def test_fieldが無いValidationErrorはfieldがnullで返る(self):
        # Arrange
        client = self._client_raising(ValidationError("ffmpeg が見つかりません。"))

        # Act
        res = client.get("/api/_raise")

        # Assert
        self.assertEqual(res.status_code, 422)
        self.assertEqual(res.json(), {"errors": [{"field": None, "message": "ffmpeg が見つかりません。"}]})


class TestCors(unittest.TestCase):
    def setUp(self):
        self.client = _local_client()

    def _preflight(self, origin: str):
        return self.client.options(
            "/api/health",
            headers={"Origin": origin, "Access-Control-Request-Method": "GET"},
        )

    def test_Viteのdevサーバーからのリクエストは許可される(self):
        # Act
        res = self._preflight("http://localhost:5173")

        # Assert
        self.assertEqual(res.headers.get("access-control-allow-origin"), "http://localhost:5173")

    def test_それ以外のoriginからのリクエストは許可されない(self):
        # Act
        res = self._preflight("http://evil.example.com")

        # Assert
        self.assertNotIn("access-control-allow-origin", res.headers)


class TestDocs(unittest.TestCase):
    def test_docsを開くとSwaggerUIが返る(self):
        # Arrange
        client = _local_client()

        # Act
        res = client.get("/docs")

        # Assert
        self.assertEqual(res.status_code, 200)


class TestMain(unittest.TestCase):
    def _run_main(self, argv: list[str]) -> dict:
        from api.__main__ import main

        with patch("api.__main__.uvicorn.run") as run:
            main(argv)
        return run.call_args.kwargs

    def test_引数なしで起動すると127_0_0_1の8000番で待ち受ける(self):
        # Act
        kwargs = self._run_main([])

        # Assert
        self.assertEqual((kwargs["host"], kwargs["port"]), ("127.0.0.1", 8000))

    def test_portを指定するとそのポートで127_0_0_1だけ待ち受ける(self):
        # Act
        kwargs = self._run_main(["--port", "9000"])

        # Assert
        self.assertEqual((kwargs["host"], kwargs["port"]), ("127.0.0.1", 9000))

    def test_hostを指定すると起動せずに終了する(self):
        # Act / Assert
        with self.assertRaises(SystemExit):
            self._run_main(["--host", "0.0.0.0"])


class TestTrustedHost(unittest.TestCase):
    def setUp(self):
        self.client = _local_client()

    def _get_health(self, host: str):
        return self.client.get("/api/health", headers={"Host": host})

    def test_Hostがevil_exampleのリクエストは400で拒否される(self):
        # Act
        res = self._get_health("evil.example")

        # Assert
        self.assertEqual(res.status_code, 400)

    def test_Hostが127_0_0_1のリクエストは通る(self):
        # Act
        res = self._get_health("127.0.0.1:8000")

        # Assert
        self.assertEqual(res.status_code, 200)

    def test_Hostがlocalhostのリクエストは通る(self):
        # Act
        res = self._get_health("localhost:8000")

        # Assert
        self.assertEqual(res.status_code, 200)

    def test_Viteのdevサーバー経由のHostのリクエストは通る(self):
        # Act
        res = self._get_health("localhost:5173")

        # Assert
        self.assertEqual(res.status_code, 200)

    def test_localhostで終わる別ドメインのHostは拒否される(self):
        # Act
        res = self._get_health("localhost.evil.example")

        # Assert
        self.assertEqual(res.status_code, 400)


class TestJsonOnlyBody(unittest.TestCase):
    def setUp(self):
        app = create_app()

        @app.post("/api/_echo")
        def _echo(payload: dict) -> dict:
            return payload

        self.client = _local_client(app)

    def test_JSONのPOSTは受け付けられる(self):
        # Act
        res = self.client.post("/api/_echo", json={"input_file": "in.mp4"})

        # Assert
        self.assertEqual(res.status_code, 200)

    def test_charsetつきのJSONのPOSTは受け付けられる(self):
        # Act
        res = self.client.post(
            "/api/_echo",
            content=b'{"input_file": "in.mp4"}',
            headers={"Content-Type": "application/json; charset=utf-8"},
        )

        # Assert
        self.assertEqual(res.status_code, 200)

    def test_フォーム送信のPOSTは415で拒否される(self):
        # Act
        res = self.client.post("/api/_echo", data={"input_file": "in.mp4"})

        # Assert
        self.assertEqual(res.status_code, 415)

    def test_text_plainのPOSTは415で拒否される(self):
        # Act
        res = self.client.post(
            "/api/_echo", content=b'{"input_file": "in.mp4"}', headers={"Content-Type": "text/plain"}
        )

        # Assert
        self.assertEqual(res.status_code, 415)

    def test_Content_Typeの無いPOSTは415で拒否される(self):
        # Act
        res = self.client.post("/api/_echo", content=b'{"input_file": "in.mp4"}')

        # Assert
        self.assertEqual(res.status_code, 415)

    def test_GETはContent_Typeが無くても通る(self):
        # Act
        res = self.client.get("/api/health")

        # Assert
        self.assertEqual(res.status_code, 200)
