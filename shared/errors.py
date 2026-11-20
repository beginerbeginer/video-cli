class ValidationError(Exception):
    # field は省略可能にする。必須にすると validation/ の既存の呼び出しを全部書き換えることになり、
    # どの Form のどの項目かは validator ではなく usecase 側でしか分からないため。
    def __init__(self, message: str, field: str | None = None) -> None:
        super().__init__(message)
        self.field = field


class FfmpegExecutionError(Exception):
    def __init__(self, message: str, detail: str | None = None) -> None:
        super().__init__(message)
        self.detail = detail
