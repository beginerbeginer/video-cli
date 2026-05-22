from collections.abc import Callable

from domain import operations
from ffmpeg.probe import ensure_ffmpeg_installed, ensure_ffprobe_installed
from shared.errors import FfmpegExecutionError, ValidationError
from ui.main_menu import prompt_main_menu
from usecases.concat_flow import run_concat_flow
from usecases.resize_flow import run_resize_flow
from usecases.trim_flow import run_trim_flow
from usecases.audio_extract_flow import run_audio_extract_flow
from usecases.gif_flow import run_gif_flow
from usecases.convert_flow import run_convert_flow
from usecases.mute_flow import run_mute_flow
from usecases.speed_flow import run_speed_flow
from usecases.thumbnail_flow import run_thumbnail_flow
from usecases.volume_flow import run_volume_flow

OperationHandler = Callable[[], None]


def exit_program() -> None:
    print("終了しました。")


def show_unknown_operation() -> None:
    print("未対応の操作です。")


def build_operation_handlers() -> dict[str, OperationHandler]:
    return {
        operations.TRIM: run_trim_flow,
        operations.CONCAT: run_concat_flow,
        operations.RESIZE: run_resize_flow,
        operations.VOLUME: run_volume_flow,
        operations.AUDIO_EXTRACT: run_audio_extract_flow,
        operations.THUMBNAIL: run_thumbnail_flow,
        operations.GIF: run_gif_flow,
        operations.SPEED: run_speed_flow,
        operations.MUTE: run_mute_flow,
        operations.CONVERT: run_convert_flow,
        operations.EXIT: exit_program,
    }


def dispatch_operation(
    operation: str,
    handlers: dict[str, OperationHandler],
    unknown_handler: OperationHandler,
) -> None:
    handler = handlers.get(operation, unknown_handler)
    handler()


def main() -> None:
    try:
        ensure_ffmpeg_installed()
        ensure_ffprobe_installed()

        handlers = build_operation_handlers()

        while True:
            operation = prompt_main_menu()
            if operation == operations.EXIT:
                exit_program()
                break
            dispatch_operation(operation, handlers, show_unknown_operation)

    except ValidationError as exc:
        print("エラーが発生しました。")
        print(str(exc))

    except FfmpegExecutionError as exc:
        print("FFmpeg を実行できませんでした。")
        print(str(exc))
        if exc.detail:
            print("詳細:")
            print(exc.detail)

    except KeyboardInterrupt:
        print("\n処理を中止しました。")


if __name__ == "__main__":
    main()
