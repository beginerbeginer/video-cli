import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from api.app import create_app
from domain import operations
from shared.errors import ValidationError


def _which_only(*available: str):
    return lambda name: f"/usr/bin/{name}" if name in available else None


class TestHealth(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(create_app())

    def test_reports_both_tools_available(self):
        with patch("ffmpeg.probe.shutil.which", side_effect=_which_only("ffmpeg", "ffprobe")):
            res = self.client.get("/api/health")

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json(), {"ffmpeg": True, "ffprobe": True})

    def test_reports_missing_ffprobe(self):
        with patch("ffmpeg.probe.shutil.which", side_effect=_which_only("ffmpeg")):
            res = self.client.get("/api/health")

        self.assertEqual(res.json(), {"ffmpeg": True, "ffprobe": False})


class TestOperations(unittest.TestCase):
    def test_lists_operations_in_menu_order_without_exit(self):
        res = TestClient(create_app()).get("/api/operations")

        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(body[0], {"id": operations.TRIM, "label": "動画を切り出す"})
        self.assertEqual(body[-1], {"id": operations.FPS, "label": "フレームレートを変換する"})
        self.assertEqual(len(body), 15)
        self.assertNotIn(operations.EXIT, [item["id"] for item in body])


class TestValidationErrorHandler(unittest.TestCase):
    def _client_raising(self, exc: Exception) -> TestClient:
        app = create_app()

        @app.get("/api/_raise")
        def _raise():
            raise exc

        return TestClient(app)

    def test_returns_422_with_field(self):
        exc = ValidationError("開始時刻の形式が正しくありません。")
        exc.field = "start_raw"

        res = self._client_raising(exc).get("/api/_raise")

        self.assertEqual(res.status_code, 422)
        self.assertEqual(
            res.json(),
            {"errors": [{"field": "start_raw", "message": "開始時刻の形式が正しくありません。"}]},
        )

    def test_field_is_null_when_not_set(self):
        res = self._client_raising(ValidationError("ffmpeg が見つかりません。")).get("/api/_raise")

        self.assertEqual(res.status_code, 422)
        self.assertEqual(res.json(), {"errors": [{"field": None, "message": "ffmpeg が見つかりません。"}]})


class TestCors(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(create_app())

    def _preflight(self, origin: str):
        return self.client.options(
            "/api/health",
            headers={"Origin": origin, "Access-Control-Request-Method": "GET"},
        )

    def test_allows_vite_dev_server(self):
        res = self._preflight("http://localhost:5173")

        self.assertEqual(res.headers.get("access-control-allow-origin"), "http://localhost:5173")

    def test_rejects_other_origin(self):
        res = self._preflight("http://evil.example.com")

        self.assertNotIn("access-control-allow-origin", res.headers)


class TestDocs(unittest.TestCase):
    def test_docs_is_served(self):
        res = TestClient(create_app()).get("/docs")

        self.assertEqual(res.status_code, 200)


class TestMain(unittest.TestCase):
    def test_listens_on_localhost_8000_by_default(self):
        from api.__main__ import main

        with patch("api.__main__.uvicorn.run") as run:
            main([])

        _, kwargs = run.call_args
        self.assertEqual(kwargs["host"], "127.0.0.1")
        self.assertEqual(kwargs["port"], 8000)

    def test_accepts_port_option(self):
        from api.__main__ import main

        with patch("api.__main__.uvicorn.run") as run:
            main(["--port", "9000"])

        _, kwargs = run.call_args
        self.assertEqual(kwargs["host"], "127.0.0.1")
        self.assertEqual(kwargs["port"], 9000)

    def test_has_no_host_option(self):
        from api.__main__ import main

        with self.assertRaises(SystemExit):
            main(["--host", "0.0.0.0"])
