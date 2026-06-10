from collections.abc import Callable

from domain import operations
from ffmpeg.probe import ensure_ffmpeg_installed, ensure_ffprobe_installed
from shared.errors import FfmpegExecutionError, ValidationError
from ui.cli.cli_ui import CliUI
from ui.cli.main_menu import prompt_main_menu
from usecases.audio_extract_flow import run_audio_extract_flow
from usecases.compress_flow import run_compress_flow
from usecases.concat_flow import run_concat_flow
from usecases.convert_flow import run_convert_flow
from usecases.crop_flow import run_crop_flow
from usecases.fps_flow import run_fps_flow
from usecases.gif_flow import run_gif_flow
from usecases.info_flow import run_info_flow
from usecases.mute_flow import run_mute_flow
from usecases.resize_flow import run_resize_flow
from usecases.rotate_flow import run_rotate_flow
from usecases.speed_flow import run_speed_flow
from usecases.thumbnail_flow import run_thumbnail_flow
from usecases.trim_flow import run_trim_flow
from usecases.ui_port import UIPort
from usecases.volume_flow import run_volume_flow

OperationHandler = Callable[[], None]


def exit_program() -> None:
    print("終了しました。")


def show_unknown_operation() -> None:
    print("未対応の操作です。")


def build_operation_handlers(ui: UIPort) -> dict[str, OperationHandler]:
    return {
        operations.TRIM: lambda: run_trim_flow(ui),
        operations.CONCAT: lambda: run_concat_flow(ui),
        operations.RESIZE: lambda: run_resize_flow(ui),
        operations.VOLUME: lambda: run_volume_flow(ui),
        operations.AUDIO_EXTRACT: lambda: run_audio_extract_flow(ui),
        operations.THUMBNAIL: lambda: run_thumbnail_flow(ui),
        operations.GIF: lambda: run_gif_flow(ui),
        operations.SPEED: lambda: run_speed_flow(ui),
        operations.MUTE: lambda: run_mute_flow(ui),
        operations.CONVERT: lambda: run_convert_flow(ui),
        operations.ROTATE: lambda: run_rotate_flow(ui),
        operations.INFO: lambda: run_info_flow(ui),
        operations.CROP: lambda: run_crop_flow(ui),
        operations.COMPRESS: lambda: run_compress_flow(ui),
        operations.FPS: lambda: run_fps_flow(ui),
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

        ui = CliUI()
        handlers = build_operation_handlers(ui)

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
