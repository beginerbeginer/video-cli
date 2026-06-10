from __future__ import annotations

import dataclasses
import json
import subprocess
from pathlib import Path

from flask import Flask, Response, jsonify, request, send_from_directory

from domain.trim_range import TrimRange
from ffmpeg.commands import (
    build_audio_extract_command,
    build_compress_command,
    build_concat_copy_command,
    build_convert_command,
    build_crop_command,
    build_fps_command,
    build_gif_command,
    build_mute_command,
    build_resize_command,
    build_rotate_command,
    build_speed_command,
    build_thumbnail_command,
    build_trim_command,
    build_volume_command,
    create_concat_list_file,
)
from ffmpeg.probe import probe_media_info
from validation.value_validators import parse_time_input

STATIC_DIR = Path(__file__).parent / "static"

app = Flask(__name__, static_folder=str(STATIC_DIR))


@app.route("/")
def index():
    return send_from_directory(STATIC_DIR, "index.html")


@app.route("/api/probe", methods=["POST"])
def probe():
    data = request.get_json(force=True) or {}
    file_path = data.get("file_path", "")
    try:
        info = probe_media_info(file_path)
        result = {
            "duration": info.duration_seconds,
            "format": info.format_name,
            "width": info.video.width if info.video else None,
            "height": info.video.height if info.video else None,
            "video_codec": info.video.codec_name if info.video else None,
            "audio_codec": info.audio.codec_name if info.audio else None,
            "fps": info.video.fps if info.video else None,
        }
        return jsonify({"ok": True, "info": result})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@app.route("/api/preview", methods=["POST"])
def preview():
    data = request.get_json(force=True) or {}
    operation = data.get("operation", "")
    params = data.get("params", {})
    try:
        if operation == "concat":
            raw_files = params.get("input_files", "a.mp4, b.mp4")
            files = [f.strip() for f in raw_files.split(",") if f.strip()]
            cmd = build_concat_copy_command("/tmp/concat_list.txt", params.get("output_file", "out.mp4"))
            cmd[cmd.index("/tmp/concat_list.txt")] = "<concat_list>"
            return jsonify({"ok": True, "command": " ".join(cmd)})
        command = _build_command(operation, params)
        return jsonify({"ok": True, "command": " ".join(command)})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)})


@app.route("/api/run", methods=["POST"])
def run():
    data = request.get_json(force=True) or {}
    operation = data.get("operation", "")
    params = data.get("params", {})

    if operation == "info":
        return _run_info(params)
    if operation == "concat":
        return _run_concat(params)

    try:
        command = _build_command(operation, params)
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400

    return _stream_command(command)


def _build_command(operation: str, params: dict) -> list[str]:
    p = params
    match operation:
        case "trim":
            start = parse_time_input(p.get("start_time", "10"))
            end = parse_time_input(p.get("end_time", "30"))
            return build_trim_command(p["input_file"], p["output_file"], TrimRange.create(start, end))
        case "resize":
            return build_resize_command(p["input_file"], p["output_file"], int(p["width"]), int(p["height"]))
        case "volume":
            return build_volume_command(p["input_file"], p["output_file"], float(p["volume_level"]))
        case "audio_extract":
            return build_audio_extract_command(p["input_file"], p["output_file"])
        case "thumbnail":
            ts = parse_time_input(p.get("timestamp", "5"))
            return build_thumbnail_command(p["input_file"], p["output_file"], ts)
        case "gif":
            return build_gif_command(p["input_file"], p["output_file"], int(p["fps"]), int(p["width"]))
        case "speed":
            return build_speed_command(p["input_file"], p["output_file"], float(p["speed"]))
        case "mute":
            return build_mute_command(p["input_file"], p["output_file"])
        case "convert":
            return build_convert_command(p["input_file"], p["output_file"])
        case "rotate":
            return build_rotate_command(p["input_file"], p["output_file"], p.get("direction", "right90"))
        case "fps":
            return build_fps_command(p["input_file"], p["output_file"], float(p["fps"]))
        case "compress":
            return build_compress_command(p["input_file"], p["output_file"], int(p.get("crf", 23)))
        case "crop":
            return build_crop_command(
                p["input_file"], p["output_file"],
                int(p["width"]), int(p["height"]),
                int(p.get("x", 0)), int(p.get("y", 0)),
            )
        case _:
            raise ValueError(f"未対応の操作: {operation}")


def _run_info(params: dict) -> Response:
    def generate():
        try:
            info = probe_media_info(params.get("input_file", ""))
            lines = [
                f"ファイル: {info.path}",
                f"長さ: {info.duration_seconds:.1f} 秒" if info.duration_seconds else "長さ: 不明",
                f"フォーマット: {info.format_name or '不明'}",
            ]
            if info.video:
                lines += [
                    f"解像度: {info.video.width}x{info.video.height}",
                    f"映像コーデック: {info.video.codec_name}",
                    f"FPS: {info.video.fps}",
                ]
            if info.audio:
                lines.append(f"音声コーデック: {info.audio.codec_name}")
            for line in lines:
                yield f"data: {json.dumps({'log': line})}\n\n"
            yield f"data: {json.dumps({'done': True, 'returncode': 0})}\n\n"
        except Exception as exc:
            yield f"data: {json.dumps({'log': f'エラー: {exc}', 'error': True})}\n\n"
            yield f"data: {json.dumps({'done': True, 'returncode': 1})}\n\n"

    return Response(generate(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


def _run_concat(params: dict) -> Response:
    raw_files = params.get("input_files", "")
    files = [f.strip() for f in raw_files.split(",") if f.strip()]
    output_file = params.get("output_file", "")

    def generate():
        with create_concat_list_file(files) as list_path:
            command = build_concat_copy_command(list_path, output_file)
            yield from _iter_command(command)

    return Response(generate(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


def _stream_command(command: list[str]) -> Response:
    def generate():
        yield from _iter_command(command)

    return Response(generate(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


def _iter_command(command: list[str]):
    yield f"data: {json.dumps({'command': ' '.join(command)})}\n\n"
    proc = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    assert proc.stdout is not None
    for line in proc.stdout:
        stripped = line.rstrip()
        if stripped:
            yield f"data: {json.dumps({'log': stripped})}\n\n"
    proc.wait()
    yield f"data: {json.dumps({'done': True, 'returncode': proc.returncode})}\n\n"


if __name__ == "__main__":
    app.run(debug=True, port=5000, threaded=True)
