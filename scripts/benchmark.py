#!/usr/bin/env python3

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "merc-py"))
from merc import Benchmarks, ToolNotFoundError  # type: ignore

RUNS_PER_CONFIG = 5

CACHE_CONFIGS = [
    {"name": "none",  "flags": []},
    {"name": "local", "flags": ["--project"]},
    {"name": "enumeration", "flags": ["--cached"]},
]


def thread_counts(max_threads: int) -> list[int]:
    counts = []
    t = 1
    while t <= max_threads:
        counts.append(t)
        t *= 2
    return counts


def main():
    parser = argparse.ArgumentParser(
        description="Run lps2lts on every .lps file in a directory"
    )
    parser.add_argument("mcrl2_path", help="Path to the directory containing the lps2lts binary")
    parser.add_argument("lps_dir", help="Directory to search for .lps files")
    parser.add_argument("--output", "-o", default="results.ndjson", help="Output NDJSON file (default: results.ndjson)")
    parser.add_argument("--max-threads", type=int, default=os.cpu_count() or 1,
                        help="Maximum thread count (powers of 2 up to this value, default: cpu count)")
    parser.add_argument("--aut-dir", default=None,
                        help="Directory to write .aut state spaces (omit to skip writing)")
    args = parser.parse_args()

    if args.aut_dir:
        os.makedirs(args.aut_dir, exist_ok=True)

    dump_dir = os.path.dirname(os.path.abspath(args.output))

    lps2lts = os.path.join(args.mcrl2_path, "lps2lts")
    lps_files = sorted(Path(args.lps_dir).rglob("*.lps"))

    if not lps_files:
        print(f"No .lps files found in {args.lps_dir}", file=sys.stderr)
        sys.exit(1)

    benchmarks = Benchmarks(runs=RUNS_PER_CONFIG,max_threads=args.max_threads,dump_dir=dump_dir)

    for lps_file in lps_files:
        name = str(lps_file.relative_to(args.lps_dir))
        for t in thread_counts(args.max_threads):
            for cache in CACHE_CONFIGS:
                for control_flow in [True, False]:
                    flags = [f"--threads={t}", "-v"] + cache["flags"]
                    if args.aut_dir:
                        aut_file = os.path.join(args.aut_dir, f"{Path(name).stem}_threads_{t}_{cache['name']}.aut")
                        flags += [aut_file]

                    if control_flow:
                        flags += ["--control-flow"]

                    benchmarks.add(
                        name=name,
                        cache_key=f"threads_{t}_{cache['name']}_control_{control_flow}",
                        tool=lps2lts,
                        arguments=[str(lps_file)] + flags,
                        timeout=600,
                        extra={
                            "file": name,
                            "threads": t,
                            "caching": cache["name"],
                            "control_flow": control_flow,
                        },
                        threads=t
                    )

    try:
        benchmarks.run(args.output)
    except ToolNotFoundError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
