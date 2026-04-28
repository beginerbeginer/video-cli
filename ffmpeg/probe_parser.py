from fractions import Fraction

from domain.media_info import AudioStreamInfo, MediaInfo, VideoStreamInfo


def parse_fps(rate: str | None) -> float | None:
    if rate is None or rate == "0/0":
        return None

    try:
        return float(Fraction(rate))
    except Exception:
        return None


def find_stream(streams: list[dict], codec_type: str) -> dict | None:
    return next((s for s in streams if s.get("codec_type") == codec_type), None)


def extract_video_info(stream: dict | None) -> VideoStreamInfo | None:
    if stream is None:
        return None

    return VideoStreamInfo(
        codec_name=stream.get("codec_name"),
        width=stream.get("width"),
        height=stream.get("height"),
        fps=parse_fps(stream.get("avg_frame_rate")),
    )


def extract_audio_info(stream: dict | None) -> AudioStreamInfo | None:
    if stream is None:
        return None

    return AudioStreamInfo(codec_name=stream.get("codec_name"))


def extract_duration(format_info: dict) -> float | None:
    raw = format_info.get("duration")
    if raw is None:
        return None
    return float(raw)


def split_ffprobe_output(ffprobe_output: dict) -> tuple[dict, list[dict]]:
    return ffprobe_output.get("format", {}), ffprobe_output.get("streams", [])


def build_media_info(file_path: str, ffprobe_output: dict) -> MediaInfo:
    format_info, streams = split_ffprobe_output(ffprobe_output)

    return MediaInfo(
        path=file_path,
        duration_seconds=extract_duration(format_info),
        format_name=format_info.get("format_name"),
        video=extract_video_info(find_stream(streams, "video")),
        audio=extract_audio_info(find_stream(streams, "audio")),
    )
