#!/usr/bin/env python3
"""Cut local videos and shift local SRT subtitles for StreamCast evaluation."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_METADATA = ROOT / "data" / "metadata.json"
DEFAULT_QUESTIONS = ROOT / "data" / "benchmark_questions.json"
TIMING_RE = re.compile(
    r"^(?P<start>\d{1,3}:\d{2}:\d{2}[,.]\d{3})\s*-->\s*"
    r"(?P<end>\d{1,3}:\d{2}:\d{2}[,.]\d{3})(?P<settings>.*)$"
)


@dataclass
class Cue:
    start: float
    end: float
    text: list[str]
    settings: str = ""


def parse_timestamp(value: str) -> float:
    hours, minutes, rest = value.replace(".", ",").split(":")
    seconds, millis = rest.split(",")
    return int(hours) * 3600 + int(minutes) * 60 + int(seconds) + int(millis) / 1000


def format_timestamp(seconds: float) -> str:
    millis = max(0, int(round(seconds * 1000)))
    hours, millis = divmod(millis, 3_600_000)
    minutes, millis = divmod(millis, 60_000)
    secs, millis = divmod(millis, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def parse_srt(path: Path) -> list[Cue]:
    content = path.read_text(encoding="utf-8-sig").replace("\r\n", "\n").strip()
    if not content:
        return []
    cues: list[Cue] = []
    for block in re.split(r"\n{2,}", content):
        lines = block.splitlines()
        timing_index = next((i for i, line in enumerate(lines) if TIMING_RE.match(line.strip())), None)
        if timing_index is None:
            continue
        match = TIMING_RE.match(lines[timing_index].strip())
        assert match is not None
        text = lines[timing_index + 1 :]
        if not text:
            continue
        cues.append(
            Cue(
                start=parse_timestamp(match.group("start")),
                end=parse_timestamp(match.group("end")),
                text=text,
                settings=match.group("settings"),
            )
        )
    return cues


def clip_cues(cues: list[Cue], start: float, end: float) -> list[Cue]:
    clipped: list[Cue] = []
    for cue in cues:
        if cue.end <= start or cue.start >= end:
            continue
        local_start = max(cue.start, start) - start
        local_end = min(cue.end, end) - start
        if local_end <= local_start:
            continue
        clipped.append(Cue(local_start, local_end, cue.text, cue.settings))
    return clipped


def write_srt(path: Path, cues: list[Cue]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    blocks = []
    for index, cue in enumerate(cues, start=1):
        timing = f"{format_timestamp(cue.start)} --> {format_timestamp(cue.end)}{cue.settings}"
        blocks.append("\n".join([str(index), timing, *cue.text]))
    path.write_text("\n\n".join(blocks) + ("\n" if blocks else ""), encoding="utf-8")


def cut_video(source: Path, start: int, end: int, output: Path) -> None:
    if end <= start:
        raise ValueError(f"Invalid video interval: {start}-{end}")
    output.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-ss",
            str(start),
            "-i",
            str(source),
            "-t",
            str(end - start),
            "-c",
            "copy",
            "-avoid_negative_ts",
            "make_zero",
            "-movflags",
            "+faststart",
            "-loglevel",
            "error",
            str(output),
        ],
        check=True,
    )


def load_sample(path: Path, sample_id: str) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    by_id = {sample["sample_id"]: sample for sample in payload["samples"]}
    if sample_id not in by_id:
        raise KeyError(f"Unknown sample_id {sample_id} in {path}")
    return by_id[sample_id]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sample_id")
    parser.add_argument("--video", type=Path, required=True, help="Locally obtained source video")
    parser.add_argument("--srt", type=Path, required=True, help="SRT aligned to the source video")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--metadata-json", type=Path, default=DEFAULT_METADATA)
    parser.add_argument("--questions-json", type=Path, default=DEFAULT_QUESTIONS)
    args = parser.parse_args()

    metadata = load_sample(args.metadata_json, args.sample_id)
    questions = load_sample(args.questions_json, args.sample_id)
    output = args.output_dir / args.sample_id
    pretrim = metadata["preprocessing"]["pretrim"]
    pretrim_start = int(pretrim["start_seconds"])
    pretrim_end = int(pretrim["end_seconds"])

    source_cues = parse_srt(args.srt)
    pretrim_cues = clip_cues(source_cues, pretrim_start, pretrim_end)
    pretrim_video = output / "pretrim" / f"{args.sample_id}.mp4"
    pretrim_srt = output / "pretrim" / f"{args.sample_id}.srt"
    cut_video(args.video, pretrim_start, pretrim_end, pretrim_video)
    write_srt(pretrim_srt, pretrim_cues)

    for task in questions["tasks"]:
        task_id = task["task_id"]
        spans = task["video_spans"]
        for setting, key in (
            ("clip", "clip_pretrim_relative_seconds"),
            ("full", "full_video_pretrim_relative_seconds"),
        ):
            span = spans[key]
            start, end = int(span["start"]), int(span["end"])
            cut_video(pretrim_video, start, end, output / setting / f"{task_id}.mp4")
            write_srt(output / setting / f"{task_id}.srt", clip_cues(pretrim_cues, start, end))


if __name__ == "__main__":
    main()
