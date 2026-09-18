"""Shared task loading, prompting, evaluation, and result persistence."""

from __future__ import annotations

import hashlib
import json
import random
import re
import tempfile
from collections import defaultdict
from pathlib import Path
from typing import Any


ANSWER_RE = re.compile(
    r"(?:answer|答案)(?:\s+is)?\s*[:：]?\s*\(?([A-D])\)?|^\s*\(?([A-D])\)?\s*[.。]?\s*$",
    re.IGNORECASE,
)


def load_backend(path: Path, config: dict[str, Any]) -> Any:
    """Load a backend module exposing create_backend(config)."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("streamcast_eval_backend", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load backend module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module, "create_backend"):
        raise AttributeError(f"{path} must define create_backend(config)")
    backend = module.create_backend(config)
    if not hasattr(backend, "generate"):
        raise AttributeError("Backend must define generate(video_path, prompt, metadata)")
    return backend


def load_backend_config(value: str | None) -> dict[str, Any]:
    if not value:
        return {}
    candidate = Path(value)
    if candidate.is_file():
        return json.loads(candidate.read_text(encoding="utf-8"))
    parsed = json.loads(value)
    if not isinstance(parsed, dict):
        raise ValueError("--backend-config must be a JSON object or a JSON file")
    return parsed


def _strip_option_label(option: str) -> str:
    return str(option).split(". ", 1)[-1].strip()


def _shuffle_question(task: dict[str, Any], language: str, seed: int) -> dict[str, Any]:
    localized = task[language]
    original_options = [_strip_option_label(value) for value in localized["options"]]
    original_answer = localized["correct_answer"].strip().upper()
    answer_index = ord(original_answer) - ord("A")
    indexed = list(enumerate(original_options))
    rng = random.Random(f"{seed}_{task['task_id']}")
    rng.shuffle(indexed)
    shuffled_options = [text for _, text in indexed]
    shuffled_answer_index = next(i for i, (old_i, _) in enumerate(indexed) if old_i == answer_index)
    return {
        "question": localized["question"].strip(),
        "options": [f"{chr(65 + i)}. {text}" for i, text in enumerate(shuffled_options)],
        "correct_answer": chr(65 + shuffled_answer_index),
    }


def build_prompt(task_id: str, task_type: str, localized: dict[str, Any], language: str) -> str:
    options = "\n".join(localized["options"])
    if language == "zh":
        return (
            "你是视频理解评测模型。请根据视频内容回答选择题。\n\n"
            "只输出一行：Answer: X，其中 X 只能是 A/B/C/D。不要输出其他内容。\n\n"
            f"Question ID: {task_id}\n"
            f"Reasoning type: {task_type}\n\n"
            f"Question:\n{localized['question']}\n\n"
            f"Options:\n{options}"
        )
    return (
        "You are a video understanding evaluation model. Answer the multiple-choice "
        "question based on the video.\n\n"
        "Output exactly one line: Answer: X, where X must be one of A/B/C/D. "
        "Do not output anything else.\n\n"
        f"Question ID: {task_id}\n"
        f"Reasoning type: {task_type}\n\n"
        f"Question:\n{localized['question']}\n\n"
        f"Options:\n{options}"
    )


def parse_answer(raw_output: str) -> str | None:
    match = ANSWER_RE.search(raw_output.strip())
    if not match:
        return None
    return (match.group(1) or match.group(2)).upper()


def load_tasks(
    questions_path: Path,
    media_root: Path,
    setting: str,
    seed: int,
) -> list[dict[str, Any]]:
    language, video_setting = setting.split("-", maxsplit=1)
    payload = json.loads(questions_path.read_text(encoding="utf-8"))
    tasks = []
    for sample in payload["samples"]:
        for task in sample["tasks"]:
            localized = _shuffle_question(task, language, seed)
            task_id = task["task_id"]
            tasks.append(
                {
                    "sample_id": sample["sample_id"],
                    "task_id": task_id,
                    "task_type": task["type"],
                    "language": language,
                    "video_setting": video_setting,
                    "video_path": media_root / sample["sample_id"] / video_setting / f"{task_id}.mp4",
                    "question": localized["question"],
                    "options": localized["options"],
                    "correct_answer": localized["correct_answer"],
                    "prompt": build_prompt(task_id, task["type"], localized, language),
                }
            )
    return tasks


def _atomic_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
        temporary = Path(handle.name)
    temporary.replace(path)


def _public_config(config: dict[str, Any]) -> dict[str, Any]:
    sensitive_names = {"api_key", "apikey", "access_token", "password", "secret"}
    public = {}
    for key, value in config.items():
        normalized = key.lower()
        sensitive = normalized in sensitive_names or normalized.endswith(
            ("_api_key", "_access_token", "_password", "_secret")
        )
        public[key] = "<redacted>" if sensitive else value
    return public


def _summary(rows: list[dict[str, Any]], total: int) -> dict[str, Any]:
    valid = [row for row in rows if row.get("predicted_answer") in {"A", "B", "C", "D"}]
    correct = sum(bool(row.get("correct")) for row in valid)
    by_type: dict[str, dict[str, int | float | None]] = {}
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in valid:
        grouped[row["task_type"]].append(row)
    for task_type, type_rows in sorted(grouped.items()):
        type_correct = sum(bool(row.get("correct")) for row in type_rows)
        by_type[task_type] = {
            "correct": type_correct,
            "total": len(type_rows),
            "accuracy": type_correct / len(type_rows),
        }
    return {
        "scheduled": total,
        "attempted": len(rows),
        "valid": len(valid),
        "errors": len(rows) - len(valid),
        "correct": correct,
        "accuracy": correct / len(valid) if valid else None,
        "by_task_type": by_type,
    }


def _normalize_response(response: Any) -> tuple[str, dict[str, Any]]:
    if isinstance(response, str):
        return response, {}
    if not isinstance(response, dict):
        raise TypeError("Backend response must be a string or dictionary")
    raw_output = response.get("raw_output", response.get("text"))
    if not isinstance(raw_output, str):
        raise TypeError("Backend response dictionary must contain string raw_output or text")
    return raw_output, {key: value for key, value in response.items() if key not in {"raw_output", "text"}}


def run_evaluation(
    *,
    backend: Any,
    backend_kind: str,
    backend_config: dict[str, Any],
    questions_path: Path,
    media_root: Path,
    setting: str,
    output_path: Path,
    seed: int,
    limit: int | None,
    max_new_tokens: int,
    dry_run: bool,
) -> dict[str, Any]:
    tasks = load_tasks(questions_path, media_root, setting, seed)
    if limit is not None:
        tasks = tasks[:limit]
    recorded_config = _public_config(backend_config)
    questions_sha256 = hashlib.sha256(questions_path.read_bytes()).hexdigest()

    previous: dict[str, Any] = {}
    if output_path.is_file():
        previous = json.loads(output_path.read_text(encoding="utf-8"))
        expected = {
            "backend_kind": backend_kind,
            "setting": setting,
            "shuffle_seed": seed,
            "questions_sha256": questions_sha256,
        }
        mismatches = [key for key, value in expected.items() if previous.get(key) != value]
        previous_model = previous.get("backend_config", {}).get("model")
        if previous_model != recorded_config.get("model"):
            mismatches.append("model")
        if mismatches:
            raise ValueError(f"Existing output is incompatible: {', '.join(mismatches)}")
    rows_by_id = {row["task_id"]: row for row in previous.get("results", [])}
    completed = {
        task_id
        for task_id, row in rows_by_id.items()
        if row.get("predicted_answer") in {"A", "B", "C", "D"}
    }

    for index, task in enumerate(tasks, start=1):
        if task["task_id"] in completed:
            continue
        video_path = task["video_path"]
        row = {
            "sample_id": task["sample_id"],
            "task_id": task["task_id"],
            "task_type": task["task_type"],
            "language": task["language"],
            "video_setting": task["video_setting"],
            "video_path": str(video_path),
            "question": task["question"],
            "options": task["options"],
            "correct_answer": task["correct_answer"],
        }
        try:
            if not dry_run and not video_path.is_file():
                raise FileNotFoundError(video_path)
            metadata = {
                "sample_id": task["sample_id"],
                "task_id": task["task_id"],
                "task_type": task["task_type"],
                "language": task["language"],
                "video_setting": task["video_setting"],
                "max_new_tokens": max_new_tokens,
            }
            response = "Answer: A" if dry_run else backend.generate(video_path, task["prompt"], metadata)
            raw_output, response_metadata = _normalize_response(response)
            predicted = parse_answer(raw_output)
            if predicted is None:
                raise ValueError(f"Could not parse answer from: {raw_output!r}")
            row.update(
                {
                    "raw_output": raw_output,
                    "predicted_answer": predicted,
                    "correct": predicted == task["correct_answer"],
                    "response_metadata": response_metadata,
                }
            )
        except Exception as error:  # Persist failures so interrupted runs lose no work.
            row.update({"predicted_answer": None, "correct": None, "error": f"{type(error).__name__}: {error}"})
        rows_by_id[task["task_id"]] = row

        ordered_rows = [rows_by_id[item["task_id"]] for item in tasks if item["task_id"] in rows_by_id]
        payload = {
            "format_version": "1.0",
            "backend_kind": backend_kind,
            "backend_config": recorded_config,
            "setting": setting,
            "shuffle_seed": seed,
            "questions_sha256": questions_sha256,
            "summary": _summary(ordered_rows, len(tasks)),
            "results": ordered_rows,
        }
        _atomic_write(output_path, payload)
        print(f"[{index}/{len(tasks)}] {task['task_id']}: {row.get('predicted_answer') or 'ERROR'}", flush=True)

    final_rows = [rows_by_id[item["task_id"]] for item in tasks if item["task_id"] in rows_by_id]
    final_payload = {
        "format_version": "1.0",
        "backend_kind": backend_kind,
        "backend_config": recorded_config,
        "setting": setting,
        "shuffle_seed": seed,
        "questions_sha256": questions_sha256,
        "summary": _summary(final_rows, len(tasks)),
        "results": final_rows,
    }
    _atomic_write(output_path, final_payload)
    close = getattr(backend, "close", None)
    if callable(close):
        close()
    return final_payload


class DryRunBackend:
    def generate(self, video_path: Path, prompt: str, metadata: dict[str, Any]) -> str:
        return "Answer: A"
