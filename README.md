# StreamCast

Official repository for *StreamCast: Benchmarking MLLMs for Future Prediction in Interactive Livestreams*.

This repository provides source metadata, bilingual benchmark questions, and offline preprocessing code. It does not redistribute videos or subtitles and does not provide media-downloading code. Users are responsible for obtaining source media in accordance with the source platform's terms and applicable law.

## Repository Structure

```text
data/
  metadata.json              Source identifiers and preprocessing timestamps
  sources.csv                Flat source metadata table
  benchmark_questions.json   Chinese and English benchmark questions
  SHA256SUMS                 Data-file checksums
  README.md                  Data schema and temporal-coordinate documentation
scripts/
  preprocess_media.py        Offline video/SRT preprocessing
```

The current release contains 470 source videos and 1,421 four-choice questions across five task types:

| Task type | Questions |
|---|---:|
| Future prediction | 470 |
| Perception localization | 312 |
| Historical understanding | 300 |
| Interaction dynamics | 221 |
| Causal attribution | 118 |

## Data Preparation

After obtaining a source video and its aligned SRT file, create the benchmark inputs with:

```bash
python scripts/preprocess_media.py AA0001 \
  --video /path/to/source.mp4 \
  --srt /path/to/source.srt \
  --output-dir /path/to/output
```

The script performs no network access. It creates the event-level pre-trim video and the task-specific clip/full-video inputs, with matching SRT files whose timestamps are clipped and shifted to start at zero.

See [data/README.md](data/README.md) for the public schema and exact timestamp semantics.

## Media Policy

Only metadata, preprocessing coordinates, and benchmark questions are released. Source videos, platform subtitles, dense descriptions, audience-action traces, model outputs, and other intermediate annotations are excluded.
