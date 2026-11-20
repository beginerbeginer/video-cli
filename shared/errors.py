class ValidationError(Exception):
    pass


class FfmpegExecutionError(Exception):
    def __init__(self, message: str, detail: str | None = None) -> None:
        super().__init__(message)
        self.detail = detail


# FfmpegExecutionError のサブクラスにしない。
# 既存の except FfmpegExecutionError がキャンセルを「失敗」として表示してしまうため。
class FfmpegCancelledError(Exception):
    pass
