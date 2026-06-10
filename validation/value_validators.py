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


def validate_fps(raw: str, label: str) -> int:
    try:
        value = int(raw)
    except ValueError as exc:
        raise ValidationError(f"{label} は整数で入力してください。") from exc

    if value < 1 or value > 60:
        raise ValidationError(f"{label} は 1〜60 の範囲で入力してください。")

    return value


def validate_gif_width(raw: str, label: str) -> int:
    try:
        value = int(raw)
    except ValueError as exc:
        raise ValidationError(f"{label} は整数で入力してください。") from exc

    if value < 16 or value > 1920:
        raise ValidationError(f"{label} は 16〜1920 の範囲で入力してください。")

    return value


def validate_speed_multiplier(raw: str, label: str) -> float:
    try:
        value = float(raw)
    except ValueError as exc:
        raise ValidationError(f"{label} は数値で入力してください。") from exc

    if value < 0.25 or value > 4.0:
        raise ValidationError(f"{label} は 0.25〜4.0 の範囲で入力してください。")

    return value


def validate_fps_rate(raw: str, label: str) -> float:
    try:
        value = float(raw)
    except ValueError as exc:
        raise ValidationError(f"{label} は数値で入力してください。") from exc

    if value < 1 or value > 120:
        raise ValidationError(f"{label} は 1〜120 の範囲で入力してください。")

    return value


def validate_crf(raw: str, label: str) -> int:
    try:
        value = int(raw)
    except ValueError as exc:
        raise ValidationError(f"{label} は整数で入力してください。") from exc

    if value < 0 or value > 51:
        raise ValidationError(f"{label} は 0〜51 の範囲で入力してください。")

    return value


def validate_timestamp_within_duration(raw: str, duration_seconds: float) -> int:
    seconds = parse_time_input(raw)
    if seconds >= duration_seconds:
        raise ValidationError(f"指定秒数 ({seconds}秒) が動画の長さ ({duration_seconds:.0f}秒) 以上です。")
    return seconds


def validate_crop_dimension(raw: str, label: str) -> int:
    try:
        value = int(raw)
    except ValueError as exc:
        raise ValidationError(f"{label} は整数で入力してください。") from exc

    if value < 2 or value > 7680:
        raise ValidationError(f"{label} は 2〜7680 の範囲で入力してください。")

    return value


def validate_crop_offset(raw: str, label: str) -> int:
    try:
        value = int(raw)
    except ValueError as exc:
        raise ValidationError(f"{label} は整数で入力してください。") from exc

    if value < 0:
        raise ValidationError(f"{label} は 0 以上の整数で入力してください。")

    return value


def validate_volume_level(raw: str, label: str) -> float:
    try:
        value = float(raw)
    except ValueError as exc:
        raise ValidationError(f"{label} は数値で入力してください。") from exc

    if value < 0.0 or value > 10.0:
        raise ValidationError(f"{label} は 0.0〜10.0 の範囲で入力してください。")

    return value
