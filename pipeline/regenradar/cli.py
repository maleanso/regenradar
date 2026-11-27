"""Command line: `regenradar run --out ./out` (local) or `regenradar run --r2` (Cloudflare R2)."""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

from .pipeline import Settings, iso, run_once
from .store import LocalStore, R2Store


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="regenradar")
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="fetch new data, render frames, write index.json, prune")
    target = r.add_mutually_exclusive_group(required=True)
    target.add_argument("--out", type=Path, help="local output directory")
    target.add_argument("--r2", action="store_true", help="write to Cloudflare R2 (env R2_*)")
    r.add_argument("--cache", type=Path, default=Path(os.environ.get("REGENRADAR_CACHE", Path.home() / ".cache" / "regenradar")),
                   help="cache for grid indexes and ICON constants")
    r.add_argument("--no-model", action="store_true", help="radar only")
    args = p.parse_args(argv)

    store = LocalStore(args.out) if args.out else R2Store()
    t0 = time.time()
    rep = run_once(store, args.cache, s=Settings(), with_model=not args.no_model)
    print(f"radar new {rep.radar_new} (errors {rep.radar_errors}), model new {rep.model_new} "
          f"(run {iso(rep.model_run) if rep.model_run else '-'}), deleted {rep.deleted}, {time.time() - t0:.1f} s")
    for n in rep.notes:
        print("note:", n)
    return 1 if rep.radar_errors and not rep.radar_new else 0


if __name__ == "__main__":
    sys.exit(main())
