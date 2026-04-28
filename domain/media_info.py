from dataclasses import dataclass


@dataclass(frozen=True)
class VideoStreamInfo:
    codec_name: str | None
    width: int | None
    height: int | None
    fps: float | None


@dataclass(frozen=True)
class AudioStreamInfo:
    codec_name: str | None


@dataclass(frozen=True)
class MediaInfo:
    path: str
    duration_seconds: float | None
    format_name: str | None
    video: VideoStreamInfo | None
    audio: AudioStreamInfo | None
