import re

from domain.trim_range import TrimRange
from shared.errors import ValidationError


def parse_hhmmss_groups(groups: tuple[str, str, str]) -> tuple[int, int, int]:
    return tuple(map(int, groups))


def hhmmss_to_seconds(hh: int, mm: int, ss: int) -> int:
    return hh * 3600 + mm * 60 + ss


def try_parse_hhmmss(raw: str) -> int | None:
    match = re.fullmatch(r"(\d{2}):(\d{2}):(\d{2})", raw)
    if match is None:
        return None

    hh, mm, ss = parse_hhmmss_groups(match.groups())
    return hhmmss_to_seconds(hh, mm, ss)


def parse_time_input(raw: str) -> int:
    if re.fullmatch(r"\d+", raw):
        return int(raw)

    result = try_parse_hhmmss(raw)
    if result is not None:
        return result

    raise ValidationError("時間の形式が不正です。HH:MM:SS または秒数で入力してください。")


def validate_trim_range(start: int, end: int) -> None:
    TrimRange.create(start, end)


def validate_dimension(raw: str, label: str) -> int:
    try:
        value = int(raw)
    except ValueError as exc:
        raise ValidationError(f"{label} は整数で入力してください。") from exc

    if value < 16 or value > 7680:
        raise ValidationError(f"{label} は 16〜7680 の範囲で入力してください。")

    return value
