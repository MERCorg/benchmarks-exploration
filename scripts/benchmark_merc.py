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
    args = parser.parse_args()

    merc_lps = os.path.join(args.merc_path, "merc-lps")
    lps_files = sorted(Path(args.lps_dir).rglob("*.lps"))

    if not lps_files:
        print(f"No .lps files found in {args.lps_dir}", file=sys.stderr)
        sys.exit(1)

    benchmarks = Benchmarks(runs=RUNS_PER_CONFIG,max_threads=args.max_threads,timeout=600.0)

    for lps_file in lps_files:
        name = str(lps_file.relative_to(args.lps_dir))
        for caching in ["none", "local", "global"]:
            benchmarks.add(
                name=f"{name}  {caching}",
                tool=merc_lps,
                arguments=["explore-explicit", str(lps_file), "--output", "temp.aut", "--caching", caching],
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
