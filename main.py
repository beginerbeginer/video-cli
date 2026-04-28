from collections.abc import Callable

from domain import operations
from ffmpeg.probe import ensure_ffmpeg_installed, ensure_ffprobe_installed
from shared.errors import FfmpegExecutionError, ValidationError
from ui.main_menu import prompt_main_menu
from usecases.concat_flow import run_concat_flow
from usecases.resize_flow import run_resize_flow
from usecases.trim_flow import run_trim_flow

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
