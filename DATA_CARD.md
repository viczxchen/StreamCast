# StreamCast Data Card

This Data Card documents the public artifacts accompanying *StreamCast:
Benchmarking MLLMs for Future Prediction in Interactive Livestreams*. It should
be read together with the repository README and the Ethics and Reproducibility
Statements in the paper.

StreamCast releases benchmark questions, source provenance, temporal
coordinates, and evaluation code. It does not redistribute source videos,
subtitles, audience-interaction traces, dense multimodal descriptions, or other
intermediate annotations.

## 1. Dataset overview

StreamCast evaluates near-future prediction in interactive livestreams. It
contains 470 publicly accessible archived livestream recordings referenced from
Bilibili and 1,421 bilingual four-choice questions:

| Task type | Questions |
|---|---:|
| Future prediction | 470 |
| Perception localization | 312 |
| Historical understanding | 300 |
| Interaction dynamics | 221 |
| Causal attribution | 118 |

The videos span six categories: multi-host PK, chat rooms, outdoor, gaming,
pets, and e-commerce. All benchmark questions are provided in Chinese and
English.

## 2. Public artifacts

| Artifact | Contents |
|---|---|
| `data/benchmark_questions.json` | Tasks grouped by sample. Each task contains `task_id`, `type`, `prediction_cutoff`, task-specific `video_spans`, and Chinese/English objects containing `question`, `options`, and `correct_answer`. |
| `data/metadata.json` | Source identifiers and provenance, selected video-part information, reported duration, pre-trim coordinates, coordinate-system definitions, and the media-policy statement. |
| `data/sources.csv` | A flat tabular view of the principal source and preprocessing fields. |
| `scripts/preprocess_media.py` | An offline utility for constructing video inputs from a locally obtained source video and the released temporal coordinates. It can also clip and shift a user-supplied aligned SRT. |
| `evaluation/` | Shared task loading, deterministic option shuffling, prompting, answer parsing, and API/local-model evaluation entry points. |
| Repository documentation | File schemas, temporal-coordinate semantics, preprocessing instructions, and evaluation interfaces. |

The public question file does **not** contain reference explanations, evidence
chains, diagnostic rationales, dense descriptions, transcripts, or internal
processing records.

## 3. Withheld artifacts

The following artifacts are not released:

- Source videos, derived clips, and platform subtitles.
- Dense visual/audio descriptions and ASR transcripts used during construction.
- Per-frame audience-interaction extractions, including audience account names
  and verbatim user-attributed interaction records.
- Automated media-acquisition or scraping code.
- Intermediate model outputs and processing artifacts.
- Annotator-identifiable quality-assessment records; the paper reports only
  aggregate human-evaluation statistics.

These exclusions reduce redistribution, copyright, and privacy risks. They also
mean that multimodal evaluation depends on the continued availability of
third-party source videos.

## 4. Source provenance and selection

All 470 recordings were collected from publicly accessible Bilibili archive
pages. Each sample is identified by a Bilibili `bvid`, source URL, and temporal
coordinates. Collection retained recordings that preserved the temporal flow
of a livestream and excluded substantially edited or post-produced videos.

The `content_origin_platform` field records `douyin` or `unknown`. Many source
pages are Bilibili archives or re-uploads of streams that originally appeared
on Douyin. Public availability on Bilibili does not establish that an uploader
owns the content or that every depicted person or original creator consented to
research use. StreamCast does not independently verify the complete chain of
authorization for third-party uploads.

The authors do not host, mirror, or redistribute the referenced media. A source
may change or disappear after release.

## 5. Rights and licensing scope

StreamCast claims no ownership of the referenced videos or subtitles. Rights in
those materials remain with their respective rights holders and may be subject
to Bilibili's terms and, where applicable, the terms and rights associated with
the original platform.

Any license applied to this repository covers only the repository materials to
which the authors can grant rights, such as authored questions, metadata,
documentation, and code. It does not grant permission to download, reproduce,
cache, or redistribute third-party videos or subtitles. Users must independently
ensure that their access and processing comply with applicable platform terms,
law, and rights-holder permissions.

**Release requirement:** explicit licenses for the authored data/documentation
and code must be added as repository license files before the final public
release. Until then, the repository should not imply that CC BY 4.0 or MIT has
already been granted.

## 6. Personal information and identity minimization

Livestreams are produced in uncontrolled real-world settings and may contain
faces, voices, public aliases, audience interactions, and bystanders. StreamCast
uses the following data-minimization measures:

- It does not release dedicated uploader fields, uploader account IDs, profile
  URLs, audience usernames, audience account IDs, or profile images.
- It does not release the internal per-user audience-interaction traces.
- Public-facing streamer names or aliases may remain when they occur in source
  titles or are necessary to distinguish participants and preserve the meaning
  or answerability of a question.
- Released `bvid` identifiers and URLs link to the original public Bilibili
  pages and can therefore reveal information displayed on those pages.
- Short, unattributed utterances or audience reactions may appear in a question
  when necessary for the task, but they are not accompanied by audience account
  identifiers.
- No face redaction is performed because the videos themselves are not
  redistributed.

The release is therefore **identity-minimized, not fully anonymized**. It must
not be used to profile or re-identify streamers, audience members, or depicted
individuals.

## 7. Evaluation inputs and preprocessing

The model evaluations reported in the paper use video as the multimodal input;
they do not require subtitles. Exact video intervals are determined by the
released source-video and pre-trim-relative coordinates.

The current preprocessing utility accepts both a local video and an aligned SRT
and emits matching MP4/SRT files. The SRT is used only to construct optional,
time-shifted subtitle artifacts: it does not affect the video boundaries or the
reported video-only evaluation protocol. Reproducing the evaluation videos
requires an independently and lawfully obtained source video, not the authors'
internal subtitle file.

Because source encodings may change and media are not redistributed, byte-level
reconstruction is not guaranteed. The released coordinates, re-encoding
settings, questions, prompts, option-shuffling procedure, and scoring code are
provided to support protocol-level reproduction.

## 8. Answer-option ordering

`benchmark_questions.json` preserves the canonical option order used during
task construction and is not position-balanced. The official evaluation loader
deterministically shuffles options for every task, using the configured seed and
`task_id`, and remaps the correct-answer label. With the default seed
`20260705`, the correct-answer positions are A/B/C/D = 362/338/362/359.

Reported evaluations should use the official loader or reproduce the same
shuffling procedure. Evaluating the unshuffled storage order would introduce a
substantial answer-position bias and would not reproduce the protocol in the
paper.

## 9. Availability, versioning, and link rot

Each source is referenced by a stable Bilibili `bvid`, but stable identifiers do
not guarantee continued access. If a source becomes unavailable, its questions
remain useful for auditing benchmark structure but cannot be included in a valid
multimodal evaluation without the corresponding media.

Unavailable or retired sources should be recorded in a versioned availability
manifest. Removing or replacing a source changes the evaluated item set;
replacement items must therefore be introduced in a new benchmark version and
must not be treated as identical to retired items. Reports should identify the
benchmark version and unavailable-item policy used for scoring.

## 10. Takedown and correction policy

Rights holders, depicted individuals, original creators, uploaders, or platform
representatives may report a source for takedown or correction through the
project repository's designated contact channel. During double-blind review,
the public release and its contact mechanism must remain anonymous.

After a request is reasonably validated, maintainers will remove the relevant
source link and derived benchmark artifacts from subsequent public releases,
record the change in the version history, and delete any author-controlled local
copy that they are required or authorized to delete. Because StreamCast does
not redistribute media, removal of a Bilibili page also makes the linked source
unavailable through the benchmark.

The authors cannot remotely delete copies independently obtained or retained by
third parties. Users remain responsible for responding to applicable platform
or rights-holder notices concerning their own copies.

## 11. Intended use and limitations

Intended uses include academic evaluation and analysis of multimodal models'
near-future prediction, long-video understanding, and livestream understanding.
Out-of-scope uses include surveillance, identity profiling, re-identification,
harassment, commercial impersonation, or other uses that may harm people shown
in or associated with the source recordings.

The dataset has several important limitations:

- It covers one acquisition platform and primarily Chinese-language content.
- Its category distribution is imbalanced and favors interaction-rich moments.
- Some Bilibili pages archive content that originated on another platform.
- Source availability is controlled by third parties.
- The release is identity-minimized but remains linkable to public source pages.
- The questions and annotations were produced with substantial model assistance,
  and human quality assessment covers a sampled subset rather than every item.
- Multiple-choice prediction evaluates a constrained candidate space rather
  than the full distribution of possible futures.

Source recordings may contain offensive, sensitive, or otherwise inappropriate
material. StreamCast does not claim exhaustive content filtering. Users should
assess these risks before accessing linked media.

## 12. Maintenance

The StreamCast author team maintains the benchmark. Availability changes,
corrections, and retired items should be documented through versioned releases
and a public change history. A stable, non-identifying contact mechanism should
be listed in the anonymous review release and replaced with the long-term
project contact in the de-anonymized release.
