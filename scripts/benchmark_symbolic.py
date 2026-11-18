#!/usr/bin/env python3

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "merc-py"))
from merc import Benchmarks, ToolNotFoundError  # type: ignore

LPSREACH_STRATEGIES = {
    "breadth-first": ["--parallel-groups"],
    "chaining": ["--chaining"],
    "saturation": ["--parallel-saturation"],
    "reach": ["--reach"],
}


def thread_counts(max_threads: int) -> list[int]:
    counts = []
    t = 1
    while t <= max_threads:
        counts.append(t)
        t *= 2
    return counts


def main():
    parser = argparse.ArgumentParser(
        description="Run lpsreach symbolic exploration on every .lps file in a directory"
    )
    parser.add_argument("mcrl2_path", help="Path to the directory containing the lpsreach binary")
    parser.add_argument("lps_dir", help="Directory to search for .lps files")
    parser.add_argument("--output", "-o", default="results.ndjson", help="Output NDJSON file (default: results.ndjson)")
    parser.add_argument("--max-threads", type=int, default=1,
                        help="Maximum thread count")
    parser.add_argument("--runs", type=int, default=5,
                        help="Number of runs per configuration (default: 5)")
    args = parser.parse_args()

    dump_dir = os.path.dirname(os.path.abspath(args.output))
    lps_files = sorted(Path(args.lps_dir).rglob("*.lps"))

    if not lps_files:
        print(f"No .lps files found in {args.lps_dir}", file=sys.stderr)
        sys.exit(1)

    lpsreach = os.path.join(args.mcrl2_path, "lpsreach")
    benchmarks = Benchmarks(runs=args.runs, max_threads=args.max_threads, dump_dir=dump_dir)

    for lps_file in lps_files:
        name = str(lps_file.relative_to(args.lps_dir))
        for t in thread_counts(args.max_threads):
            for strategy, strategy_args in LPSREACH_STRATEGIES.items():
                arguments = ["--groups=used", "--cached", *strategy_args, "--timings", f"--threads={t}"]

                if t > 1:
                    arguments += ["--parallel-learning"]

                arguments += [str(lps_file)]

                benchmarks.add(
                    name=name,
                    cache_key=f"lpsreach_{strategy}_{t}",
                    tool=lpsreach,
                    arguments=arguments,
                    threads=t,
                    timeout=600,
                    extra={
                        "file": name,
                        "tool": "lpsreach",
                        "strategy": strategy,
                        "threads": t,
                    },
                )

    try:
        benchmarks.run(args.output)
    except ToolNotFoundError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
