from domain.media_fingerprint import MediaFingerprint
from domain.media_info import MediaInfo
from shared.errors import ValidationError


def validate_trim_end_within_duration(end_seconds: int, media_info: MediaInfo) -> None:
    if media_info.duration_seconds is None:
        return

    if end_seconds > int(media_info.duration_seconds):
        raise ValidationError("終了時間が動画の長さを超えています。")


def are_concat_streams_compatible(media_infos: list[MediaInfo]) -> bool:
    if len(media_infos) < 2:
        return True

    first = MediaFingerprint.from_media_info(media_infos[0])
    return all(
        MediaFingerprint.from_media_info(current) == first
        for current in media_infos[1:]
    )


def format_video_desc(media: MediaInfo) -> str:
    if media.video is None:
        return "なし"
    return (
        f"{media.video.codec_name}, "
        f"{media.video.width}x{media.video.height}, "
        f"{media.video.fps}"
    )


def format_audio_desc(media: MediaInfo) -> str:
    if media.audio is None:
        return "なし"
    return media.audio.codec_name or "不明"


def format_compatibility_entry(index: int, media: MediaInfo) -> str:
    return (
        f"- 入力{index}: "
        f"container={media.format_name}, "
        f"video={format_video_desc(media)}, "
        f"audio={format_audio_desc(media)}"
    )


def format_compatibility_verdict(compatible: bool) -> str:
    if compatible:
        return "- 判定: 互換あり。copy 結合を試行します。"
    return "- 判定: 互換なし。再エンコード結合に切り替えます。"


def build_concat_compatibility_report(media_infos: list[MediaInfo]) -> str:
    entries = [
        format_compatibility_entry(i, m)
        for i, m in enumerate(media_infos, start=1)
    ]
    verdict = format_compatibility_verdict(
        are_concat_streams_compatible(media_infos)
    )
    return "\n".join(["結合互換性チェック結果:"] + entries + [verdict])
