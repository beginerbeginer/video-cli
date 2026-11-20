from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from domain import operations
from ffmpeg.probe import ensure_ffmpeg_installed, ensure_ffprobe_installed
from shared.errors import ValidationError

# Why not "*": PC 内のファイルを扱う API なので、Vite の dev サーバー以外のページから叩かれたくない。
DEV_CORS_ORIGINS = ["http://localhost:5173"]


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
