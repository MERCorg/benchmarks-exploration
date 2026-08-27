#!/usr/bin/env python3

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "merc-py"))
from merc import Benchmarks, ToolNotFoundError  # type: ignore

def thread_counts(max_threads: int) -> list[int]:
    counts = []
    t = 1
    while t <= max_threads:
        counts.append(t)
        t *= 2
    return counts

def main():
    parser = argparse.ArgumentParser(
        description="Run merc-lps on every .lps file in a directory"
    )
    parser.add_argument("merc_path", help="Path to the directory containing the merc-lps binary")
    parser.add_argument("lps_dir", help="Directory to search for .lps files")
    parser.add_argument("--output", "-o", default="results.ndjson", help="Output NDJSON file (default: results.ndjson)")
    parser.add_argument("--max-threads", type=int, default=1,
                        help="Maximum thread count")
    parser.add_argument("--aut-dir", default=None,
                        help="Directory to write .aut state spaces (omit to skip writing)")
    parser.add_argument("--runs", type=int, default=5,
                        help=f"Number of runs per configuration (default: 5)")
    args = parser.parse_args()

    if args.aut_dir:
        os.makedirs(args.aut_dir, exist_ok=True)

    dump_dir = os.path.dirname(os.path.abspath(args.output))
    merc_lps = os.path.join(args.merc_path, "merc-lps")
    lps_files = sorted(Path(args.lps_dir).rglob("*.lps"))

    if not lps_files:
        print(f"No .lps files found in {args.lps_dir}", file=sys.stderr)
        sys.exit(1)

    benchmarks = Benchmarks(runs=args.runs, max_threads=args.max_threads, dump_dir=dump_dir)

    for lps_file in lps_files:
        name = str(lps_file.relative_to(args.lps_dir))
        for t in thread_counts(args.max_threads):
            for caching in ["none", "local"]:
                for control_flow in [True, False]:
                    arguments = ["explore-explicit", str(lps_file), "--timings", "--caching", caching, "--threads", str(t)]

                    if control_flow:
                        arguments += ["--control-flow"]

                    if args.aut_dir:
                        aut_file = os.path.join(args.aut_dir, f"{Path(name).stem}_{caching}.aut")
                        arguments += ["--output", aut_file]

                    benchmarks.add(
                        name=name,
                        cache_key=f"{caching}_{control_flow}_{t}",
                        tool=merc_lps,
                        arguments=arguments,
                        threads=t,
                        timeout=600,
                        extra={
                            "file": name,
                            "caching": caching,
                            "control-flow": control_flow,
                        },
                )

    try:
        benchmarks.run(args.output)
    except ToolNotFoundError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
