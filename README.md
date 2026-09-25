# StreamCast

Official repository for *StreamCast: Benchmarking MLLMs for Future Prediction in Interactive Livestreams*.

This repository provides source metadata, bilingual benchmark questions, and offline preprocessing code. It does not redistribute videos or subtitles and does not provide media-downloading code. Users are responsible for obtaining source media in accordance with the source platform's terms and applicable law.

See [DATA_CARD.md](DATA_CARD.md) for detailed documentation of source provenance,
released and withheld artifacts, identity minimization, rights and licensing
scope, evaluation inputs, link rot, and the takedown policy.

## License

The authored benchmark questions, metadata, and documentation are licensed
under [CC BY 4.0](LICENSE-DATA). Source code is licensed under the
[MIT License](LICENSE-CODE). These licenses do not apply to third-party source
videos or subtitles, which are not redistributed by this repository.

## Repository Structure

```text
DATA_CARD.md                   Dataset documentation and release policy
CHANGELOG.md                   Versioned release and availability changes
LICENSE-CODE                   MIT license for source code
LICENSE-DATA                   CC BY 4.0 license for data and documentation
data/
  metadata.json              Source identifiers and preprocessing timestamps
  sources.csv                Flat source metadata table
  benchmark_questions.json   Chinese and English benchmark questions
  README.md                  Data schema and temporal-coordinate documentation
scripts/
  preprocess_media.py        Offline video/SRT preprocessing
evaluation/
  common.py                  Shared prompt and evaluation loop
  run_api.py                 Universal API evaluation entry point
  run_local.py               Universal local evaluation entry point
  README.md                  Backend interface and usage
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

## Evaluation

The API and local-model runners use one shared prompt and evaluate every clip/full setting one question and one video at a time. Model-specific SDK calls are isolated in small backend adapters. See [evaluation/README.md](evaluation/README.md) for the interface and commands.

## Media Policy

Only metadata, preprocessing coordinates, and benchmark questions are released. Source videos, platform subtitles, dense descriptions, audience-action traces, model outputs, and other intermediate annotations are excluded.
