from dataclasses import dataclass

from domain.media_info import AudioStreamInfo, MediaInfo, VideoStreamInfo


@dataclass(frozen=True)
class VideoSignature:
    codec_name: str | None
    width: int | None
    height: int | None
    fps: float | None

    @classmethod
    def from_video(cls, video: VideoStreamInfo | None) -> "VideoSignature | None":
        if video is None:
            return None
        return cls(
            codec_name=video.codec_name,
            width=video.width,
            height=video.height,
            fps=round(video.fps or 0.0, 3),
        )


@dataclass(frozen=True)
class AudioSignature:
    codec_name: str | None

    @classmethod
    def from_audio(cls, audio: AudioStreamInfo | None) -> "AudioSignature | None":
        if audio is None:
            return None
        return cls(codec_name=audio.codec_name)


@dataclass(frozen=True)
class MediaFingerprint:
    format_name: str | None
    video: VideoSignature | None
    audio: AudioSignature | None

    @classmethod
    def from_media_info(cls, media: MediaInfo) -> "MediaFingerprint":
        return cls(
            format_name=media.format_name,
            video=VideoSignature.from_video(media.video),
            audio=AudioSignature.from_audio(media.audio),
        )
