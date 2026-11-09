#!/usr/bin/env python3
"""Assemble frame-accurate 1080p cuts from local 24 fps H3 MP4s."""

import argparse
import hashlib
import json
import os
from fractions import Fraction
from pathlib import Path
import subprocess
import tempfile

FPS = 24
TIMESCALE = 12_288
TICKS_PER_FRAME = TIMESCALE // FPS
FFMPEG = ["ffmpeg", "-hide_banner", "-v", "error", "-nostdin", "-xerror"]
COLOR_FIELDS = ("color_range", "color_space", "color_transfer", "color_primaries")


def run(command, *, capture=False):
    result = subprocess.run(command, stdout=subprocess.PIPE if capture else None, check=True)
    return result.stdout


def probe(path, selector, *args):
    return json.loads(run([
        "ffprobe", "-v", "error", "-select_streams", selector, *args,
        "-of", "json", str(path),
    ], capture=True))


def stream(path, selector):
    streams = probe(path, selector, "-show_streams")["streams"]
    if not streams:
        raise ValueError(f"{path.name}: no {selector} stream")
    return streams[0]


def packets(path):
    return probe(path, "v:0", "-show_packets", "-show_entries", "packet=pts,duration")["packets"]


def read_manifest(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or type(data.get("fps")) is not int or data["fps"] != FPS:
        raise ValueError("Manifest fps must be 24")
    if not isinstance(data.get("shots"), list) or not data["shots"]:
        raise ValueError("Manifest shots must be a nonempty array")

    next_start, seen = 0, set()
    for shot in data["shots"]:
        if not isinstance(shot, dict):
            raise ValueError("Each shot must be an object")
        shot_id = shot.get("id")
        if not isinstance(shot_id, str) or not shot_id.strip() or shot_id in seen:
            raise ValueError("Each shot must have a unique, nonempty id")
        seen.add(shot_id)
        start, count = shot.get("start"), shot.get("frames")
        source_start = shot.setdefault("source_start", 0)
        if type(start) is not int or start != next_start:
            raise ValueError(f"{shot_id}: expected timeline start {next_start}")
        if type(count) is not int or count < 1 or type(source_start) is not int or source_start < 0:
            raise ValueError(f"{shot_id}: frames must be positive and source_start nonnegative")
        shot["source"] = local_file(path.parent, shot.get("source"), f"{shot_id}: source")
        next_start += count
    soundtrack = data.get("soundtrack")
    audio = local_file(path.parent, soundtrack, "soundtrack") if soundtrack is not None else None
    return data["shots"], audio, next_start


def local_file(parent, value, label):
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label}: expected a local file path")
    path = (parent / value).resolve()
    if not path.is_file():
        raise ValueError(f"{label}: missing file {path}")
    return path


def inspect_shot(shot):
    path = shot["source"]
    info = stream(path, "v:0")
    dimensions = (info["width"], info["height"])
    if dimensions not in {(1920, 1080), (1920, 1088)}:
        raise ValueError(f"{shot['id']}: expected 1920×1080 or 1920×1088, got {dimensions}")
    if info["avg_frame_rate"] != "24/1" or info["r_frame_rate"] != "24/1":
        raise ValueError(f"{shot['id']}: expected 24 fps")
    pts = sorted(p["pts"] for p in packets(path))
    if len(pts) < shot["source_start"] + shot["frames"]:
        raise ValueError(f"{shot['id']}: source does not cover the requested frame range")
    time_base = Fraction(info["time_base"])
    for index, timestamp in enumerate(pts):
        if (index and timestamp <= pts[index - 1]) or abs(
            (timestamp - pts[0]) * time_base - Fraction(index, FPS)
        ) > time_base:
            raise ValueError(f"{shot['id']}: source timestamps are not constant 24 fps")
    return info


def inspect_audio(path, total_frames):
    info = stream(path, "a:0")
    if info["codec_name"] != "aac" or info["start_pts"] != 0:
        raise ValueError("Soundtrack must be AAC with a stream start timestamp of zero")
    duration = info["duration_ts"] * Fraction(info["time_base"])
    if abs(duration - Fraction(total_frames, FPS)) >= Fraction(1, FPS):
        raise ValueError("Soundtrack and timeline must end less than one video frame apart")
    return duration


def encode_shot(shot, height, target):
    start, end = shot["source_start"], shot["source_start"] + shot["frames"]
    filters = [f"trim=start_frame={start}:end_frame={end}"]
    if height == 1088:
        filters.append("crop=1920:1080:0:4")
    filters += ["setsar=1", "settb=1/24", "setpts=N"]
    run([
        *FFMPEG, "-i", str(shot["source"]), "-map", "0:v:0", "-an", "-sn", "-dn",
        "-vf", ",".join(filters), "-c:v", "libx264", "-preset", "veryfast",
        "-crf", "16", "-pix_fmt", "yuv420p", "-profile:v", "high", "-bf", "0",
        "-g", "96", "-r", str(FPS), "-fps_mode", "cfr",
        "-video_track_timescale", str(TIMESCALE), str(target),
    ])


def end_in_microseconds(frames):
    return (frames * 1_000_000 + FPS // 2) // FPS


def audio_hash(path):
    data = run([*FFMPEG, "-i", str(path), "-map", "0:a:0", "-c:a", "copy",
                "-f", "adts", "-"], capture=True)
    return hashlib.sha256(data).digest()


def verify(path, total_frames, soundtrack, duration):
    video = stream(path, "v:0")
    if (video["width"], video["height"], video["avg_frame_rate"], video["time_base"]) != (
        1920, 1080, "24/1", f"1/{TIMESCALE}"
    ):
        raise ValueError("Output dimensions or video time base did not match")
    timeline = packets(path)
    if len(timeline) != total_frames or any(
        packet.get("pts") != index * TICKS_PER_FRAME or packet.get("duration") != TICKS_PER_FRAME
        for index, packet in enumerate(timeline)
    ):
        raise ValueError("Output frame count or timestamps did not match the timeline")
    if soundtrack:
        if inspect_audio(path, total_frames) != duration or audio_hash(path) != audio_hash(soundtrack):
            raise ValueError("Output soundtrack timing or AAC packets changed")
    run([*FFMPEG, "-i", str(path), "-map", "0:v:0", "-map", "0:a:0?", "-f", "null", "-"])


def assemble(shots, source_info, soundtrack, duration, total_frames, output):
    if output.suffix.lower() != ".mp4" or not output.parent.is_dir():
        raise ValueError("Output must be a new .mp4 path in an existing directory")
    if output.exists() or output.is_symlink():
        raise ValueError(f"Output already exists: {output}")
    with tempfile.TemporaryDirectory(prefix=".h3-mv-", dir=output.parent) as folder:
        folder = Path(folder)
        entries = ["ffconcat version 1.0"]
        for index, (shot, info) in enumerate(zip(shots, source_info), 1):
            name = f"shot-{index:05}.mp4"
            print(f"[{index}/{len(shots)}] {shot['id']}", flush=True)
            encode_shot(shot, info["height"], folder / name)
            start = shot["start"]
            # Round the cumulative endpoints so concat does not accumulate rounding error.
            micros = end_in_microseconds(start + shot["frames"]) - end_in_microseconds(start)
            entries.extend((f"file '{name}'", f"duration {micros // 1_000_000}.{micros % 1_000_000:06d}"))
        playlist = folder / "timeline.ffconcat"
        playlist.write_text("\n".join(entries) + "\n", encoding="ascii")
        target = folder / "verified.mp4"
        inputs = ["-f", "concat", "-safe", "1", "-i", str(playlist)]
        mapping = ["-map", "0:v:0"]
        if soundtrack:
            inputs += ["-i", str(soundtrack)]
            mapping += ["-map", "1:a:0"]
        run([
            *FFMPEG, *inputs, *mapping, "-c", "copy", "-map_metadata", "-1",
            "-map_chapters", "-1", "-video_track_timescale", str(TIMESCALE),
            "-movflags", "+faststart", str(target),
        ])
        verify(target, total_frames, soundtrack, duration)
        os.link(target, output)  # Atomically create the output without replacing an existing file.


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="validate local inputs without encoding")
    mode.add_argument("--output", type=Path, help="write a new MP4 after validating the result")
    args = parser.parse_args()

    try:
        shots, soundtrack, total_frames = read_manifest(args.manifest.resolve())
        source_info = [inspect_shot(shot) for shot in shots]
        tags = {tuple(info.get(field) for field in COLOR_FIELDS) for info in source_info}
        if len(tags) != 1:
            raise ValueError("Source color tags differ; conform the clips in an editor first")
        duration = inspect_audio(soundtrack, total_frames) if soundtrack else None
        print(f"Inputs verified: {len(shots)} shots, {total_frames} frames at {FPS} fps", flush=True)
        if args.output:
            output = args.output.absolute()
            assemble(shots, source_info, soundtrack, duration, total_frames, output)
            print(f"Verified MP4: {output}", flush=True)
    except (OSError, ValueError, KeyError, ZeroDivisionError, subprocess.CalledProcessError) as exc:
        parser.exit(1, f"assemble: {exc}\n")


if __name__ == "__main__":
    main()
