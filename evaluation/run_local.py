#!/usr/bin/env python3
"""Run StreamCast through a local-model backend, one task and one video at a time."""

from __future__ import annotations

import argparse
from pathlib import Path

from common import DryRunBackend, load_backend, load_backend_config, run_evaluation


ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backend", type=Path, help="Python backend adapter")
    parser.add_argument("--backend-config", help="JSON object or path to JSON config")
    parser.add_argument("--model", required=True, help="Model name or local checkpoint path")
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--questions", type=Path, default=ROOT / "data" / "benchmark_questions.json")
    parser.add_argument("--media-root", type=Path, required=True)
    parser.add_argument("--setting", choices=("zh-clip", "zh-full", "en-clip", "en-full"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=20260705)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--max-new-tokens", type=int, default=16)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    config = load_backend_config(args.backend_config)
    config.update(
        {"model": args.model, "device": args.device, "max_new_tokens": args.max_new_tokens}
    )
    if args.dry_run:
        backend = DryRunBackend()
    elif args.backend:
        backend = load_backend(args.backend, config)
    else:
        parser.error("--backend is required unless --dry-run is used")

    payload = run_evaluation(
        backend=backend,
        backend_kind="local",
        backend_config=config,
        questions_path=args.questions,
        media_root=args.media_root,
        setting=args.setting,
        output_path=args.output,
        seed=args.seed,
        limit=args.limit,
        max_new_tokens=args.max_new_tokens,
        dry_run=args.dry_run,
    )
    print(payload["summary"])


if __name__ == "__main__":
    main()
