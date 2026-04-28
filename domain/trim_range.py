from dataclasses import dataclass

from shared.errors import ValidationError


@dataclass(frozen=True)
class TrimRange:
    start_seconds: int
    end_seconds: int

    @classmethod
    def create(cls, start_seconds: int, end_seconds: int) -> "TrimRange":
        if start_seconds < 0:
            raise ValidationError("開始時間は 0 以上で入力してください。")
        if start_seconds >= end_seconds:
            raise ValidationError("開始時間は終了時間より前にしてください。")
        return cls(start_seconds=start_seconds, end_seconds=end_seconds)

    @property
    def duration_seconds(self) -> int:
        return self.end_seconds - self.start_seconds
