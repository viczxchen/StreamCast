# Evaluation

StreamCast provides two model-agnostic evaluation entry points:

- `run_api.py` for hosted model APIs;
- `run_local.py` for locally deployed models.

Both entry points use the same task loader, option shuffling, prompt template, answer parser, and result format from `common.py`. Every setting is evaluated **one question and one video per model call**. In particular, full-video evaluation does not group questions from the same source video.

## Media Layout

First prepare the media as described in [`data/README.md`](../data/README.md). The evaluator expects:

```text
<media_root>/<sample_id>/clip/<task_id>.mp4
<media_root>/<sample_id>/full/<task_id>.mp4
```

## Backend Interface

Model SDKs differ in upload, request, and local inference APIs. Each entry point therefore accepts a small Python adapter through `--backend`. The adapter is loaded once, so a local model can remain in memory and an API client can reuse its connection.

```python
def create_backend(config):
    return Backend(config)


class Backend:
    def __init__(self, config):
        # Initialize the API client or load the local model here.
        pass

    def generate(self, video_path, prompt, metadata):
        # Return a string, or {"raw_output": "Answer: A", "usage": {...}}.
        # metadata never contains the gold answer.
        return "Answer: A"

    def close(self):
        pass
```

Provider-specific values can be passed as a JSON object or JSON file with `--backend-config`. API adapters receive `model`, `api_key_env`, `base_url`, and `max_new_tokens`; local adapters receive `model`, `device`, and `max_new_tokens`.

## Usage

API evaluation:

```bash
python evaluation/run_api.py \
  --backend /path/to/api_backend.py \
  --backend-config '{"fps": 1}' \
  --model MODEL_NAME \
  --api-key-env PROVIDER_API_KEY \
  --media-root /path/to/preprocessed_media \
  --setting en-clip \
  --output results/MODEL_NAME__en-clip.json
```

Local evaluation:

```bash
python evaluation/run_local.py \
  --backend /path/to/local_backend.py \
  --model /path/to/checkpoint \
  --device cuda \
  --media-root /path/to/preprocessed_media \
  --setting en-full \
  --output results/MODEL_NAME__en-full.json
```

Valid settings are `zh-clip`, `zh-full`, `en-clip`, and `en-full`. Options are deterministically shuffled with seed `20260705`. Results are atomically written after every question; rerunning the same command skips valid answers and retries missing, malformed, or failed entries.

Use `--dry-run --limit 2` to verify task loading and output generation without loading a model or calling an API.
