#!/usr/bin/env python3

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "merc-py"))
from merc import Benchmarks, ToolNotFoundError  # type: ignore

RUNS_PER_CONFIG = 5

def main():
    parser = argparse.ArgumentParser(
        description="Run merc-lps on every .lps file in a directory"
    )
    parser.add_argument("merc_path", help="Path to the directory containing the merc-lps binary")
    parser.add_argument("lps_dir", help="Directory to search for .lps files")
    parser.add_argument("--output", "-o", default="results.ndjson", help="Output NDJSON file (default: results.ndjson)")
    parser.add_argument("--max-threads", type=int, default=os.cpu_count() or 1,
                        help="Maximum thread count")
    parser.add_argument("--aut-dir", default=None,
                        help="Directory to write .aut state spaces (omit to skip writing)")
    args = parser.parse_args()

    if args.aut_dir:
        os.makedirs(args.aut_dir, exist_ok=True)

    dump_dir = os.path.dirname(os.path.abspath(args.output))
    merc_lps = os.path.join(args.merc_path, "merc-lps")
    lps_files = sorted(Path(args.lps_dir).rglob("*.lps"))

    if not lps_files:
        print(f"No .lps files found in {args.lps_dir}", file=sys.stderr)
        sys.exit(1)

    benchmarks = Benchmarks(runs=RUNS_PER_CONFIG,max_threads=args.max_threads,dump_dir=dump_dir)

    for lps_file in lps_files:
        name = str(lps_file.relative_to(args.lps_dir))
        for caching in ["none", "local", "global"]:
            arguments = ["explore-explicit", str(lps_file), "--timings", "--caching", caching]
            if args.aut_dir:
                aut_file = os.path.join(args.aut_dir, f"{Path(name).stem}_{caching}.aut")
                arguments += ["--output", aut_file]
            else:
                arguments += ["--output", os.devnull]
            benchmarks.add(
                name=name,
                cache_key=caching,
                tool=merc_lps,
                arguments=arguments,
                timeout=600,
                extra={
                    "file": name,
                    "caching": caching,
                },
            )

    try:
        benchmarks.run(args.output)
    except ToolNotFoundError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
