from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from domain import operations
from ffmpeg.probe import ensure_ffmpeg_installed, ensure_ffprobe_installed
from shared.errors import ValidationError

# Why not "*": PC 内のファイルを扱う API なので、Vite の dev サーバー以外のページから叩かれたくない。
DEV_CORS_ORIGINS = ["http://localhost:5173"]
# Why not 127.0.0.1 で待ち受けるだけ: DNS リバインディングで、悪意のあるサイトのドメインが
# 127.0.0.1 を指すと、ブラウザからこの API を呼べてしまう。Host を見ればそのドメイン名が分かる。
# ポートは TrustedHostMiddleware が外して比べるので、Vite 経由（localhost:5173）もこのまま通る。
ALLOWED_HOSTS = ["127.0.0.1", "localhost"]


# Why not 本文の有無で判断: 本文が空の POST（例: ジョブのキャンセル）もほかのサイトから送れてしまう。
# 書き込み系のメソッドは一律に JSON を求め、ブラウザに CORS のプリフライトを必ず挟ませる。
BODY_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


def _is_json(content_type: str) -> bool:
    return content_type.split(";")[0].strip().lower() == "application/json"


async def _reject_non_json_body(request: Request, call_next):
    # Why not FastAPI の Body の検証に任せる: フォームや text/plain はプリフライト無しで送れるため、
    # ハンドラに届く前に断って CSRF を防ぐ。
    if request.method in BODY_METHODS and not _is_json(request.headers.get("content-type", "")):
        return JSONResponse(
            status_code=415,
            content={"errors": [{"field": None, "message": "Content-Type は application/json にしてください。"}]},
        )
    return await call_next(request)


def _is_available(ensure_installed) -> bool:
    try:
        ensure_installed()
    except ValidationError:
        return False
    return True


async def _handle_validation_error(_: Request, exc: ValidationError) -> JSONResponse:
    # Why getattr: field は #83 で ValidationError に追加されるため、まだ無い版でも動くようにする。
    field = getattr(exc, "field", None)
    return JSONResponse(status_code=422, content={"errors": [{"field": field, "message": str(exc)}]})


def create_app() -> FastAPI:
    app = FastAPI(title="video-cli API")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=DEV_CORS_ORIGINS,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.middleware("http")(_reject_non_json_body)
    # Why not 先に追加: Starlette は後に追加したミドルウェアほど外側で動く。Host の確認を一番外にする。
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=ALLOWED_HOSTS)
    app.add_exception_handler(ValidationError, _handle_validation_error)

    @app.get("/api/health")
    def health() -> dict[str, bool]:
        return {
            "ffmpeg": _is_available(ensure_ffmpeg_installed),
            "ffprobe": _is_available(ensure_ffprobe_installed),
        }

    @app.get("/api/operations")
    def list_operations() -> list[dict[str, str]]:
        return [
            {"id": operation, "label": label}
            for operation, label in operations.OPERATION_LABELS.items()
            if operation != operations.EXIT
        ]

    return app
