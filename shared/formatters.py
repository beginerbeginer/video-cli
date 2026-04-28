from domain.media_info import AudioStreamInfo, MediaInfo, VideoStreamInfo


def format_seconds_to_hhmmss(total_seconds: float | int | None) -> str:
    if total_seconds is None:
        return "不明"

    total = int(total_seconds)
    hh = total // 3600
    mm = (total % 3600) // 60
    ss = total % 60
    return f"{hh:02d}:{mm:02d}:{ss:02d}"


def format_video_line(video: VideoStreamInfo) -> str:
    codec = video.codec_name or "不明"
    width = video.width or "?"
    height = video.height or "?"
    fps = video.fps if video.fps is not None else "不明"
    return f"- 映像: codec={codec}, size={width}x{height}, fps={fps}"


def format_audio_line(audio: AudioStreamInfo) -> str:
    return f"- 音声: codec={audio.codec_name or '不明'}"


def format_media_info_summary(media_info: MediaInfo) -> str:
    lines = [
        f"- ファイル: {media_info.path}",
        f"- 長さ: {format_seconds_to_hhmmss(media_info.duration_seconds)}",
        f"- コンテナ: {media_info.format_name or '不明'}",
    ]

    if media_info.video:
        lines.append(format_video_line(media_info.video))

    if media_info.audio:
        lines.append(format_audio_line(media_info.audio))

    return "\n".join(lines)
