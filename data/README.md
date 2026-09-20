# Data Format

This directory contains source metadata and the bilingual StreamCast evaluation questions. It does not contain source media, subtitles, or intermediate model-generated annotations.

## Files

- `metadata.json`: source identifiers and event-level pre-trim coordinates for 470 videos.
- `sources.csv`: a flat version of the main source and pre-trim fields.
- `benchmark_questions.json`: 1,421 Chinese/English questions, answer choices, labels, and evaluation-video intervals.

## Metadata

Each entry in `metadata.json` contains:

- a stable sample ID and category;
- public source identifiers, URL, selected part index, title, uploader, and reported duration;
- the event-level pre-trim start and end timestamps used by the benchmark.

The metadata is provided only to identify the public source and reproduce preprocessing. Availability of third-party pages may change over time.

## Benchmark Questions

Each task in `benchmark_questions.json` contains:

- `task_id` and `type`;
- the prediction cutoff and clip/full-video intervals;
- Chinese (`zh`) and English (`en`) question text;
- four answer choices and the correct answer label.

Reference explanations, evidence chains, diagnostic rationales, dense descriptions, audience-action traces, and internal processing records are not included.

## Temporal Coordinates

All released timestamps use integer seconds. Two coordinate systems are provided:

- `source_video_seconds`: relative to the locally obtained source video.
- `pretrim_relative_seconds`: relative to the event-level pre-trim video.

The preprocessing chain is:

```text
pretrim = source_video[pretrim_start:pretrim_end]
task_clip = pretrim[clip_start:clip_end]
task_full = pretrim[full_start:full_end]
```

Therefore, a task interval `[a, b)` in pre-trim coordinates corresponds to `[pretrim_start + a, pretrim_start + b)` in source-video coordinates.

Eight historical pre-trim records requested an endpoint beyond the platform-reported duration. FFmpeg stops at end-of-file in these cases. `metadata.json` records both the requested endpoint and the effective endpoint implied by the reported duration. Every released task interval ends within the reported source duration.

## Offline Preprocessing

The preprocessing script requires a local source video and an SRT file aligned to that source:

```bash
python scripts/preprocess_media.py AA0001 \
  --video /path/to/source.mp4 \
  --srt /path/to/source.srt \
  --output-dir /path/to/output
```

It produces:

```text
AA0001/
  pretrim/AA0001.{mp4,srt}
  clip/<task_id>.{mp4,srt}
  full/<task_id>.{mp4,srt}
```

For each interval, subtitle cues outside the interval are removed, boundary-crossing cues are clipped, timestamps are shifted to start at `00:00:00,000`, and cue indices are regenerated. Video cutting uses accurate output-side seeking and H.264/AAC encoding. Re-encoding is intentional: stream-copy cuts can only start cleanly on keyframes and may otherwise include content before the requested start or omit content after it.
