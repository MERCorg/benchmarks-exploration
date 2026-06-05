#!/usr/bin/env python3

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "merc-py"))
from merc import RunProcess, TimeExceededError, MemoryExceededError, ToolNotFoundError  # type: ignore

RUNS_PER_CONFIG = 5

CACHE_CONFIGS = [
    {"name": "no_cache",     "flags": []},
    {"name": "cached",       "flags": ["--cached"]},
    {"name": "global_cache", "flags": ["--cached", "--global-cache"]},
]


def thread_counts(max_threads: int) -> list[int]:
    counts = []
    t = 1
    while t <= max_threads:
        counts.append(t)
        t *= 2
    return counts


def run_config(lps2lts: str, lps_file: str, extra_flags: list[str]) -> dict:
    try:
        proc = RunProcess(lps2lts, [lps_file] + extra_flags)
        return {"status": "ok", "time_s": proc.user_time, "memory_mb": proc.max_memory}
    except TimeExceededError as e:
        return {"status": "timeout", "time_s": e.value}
    except MemoryExceededError as e:
        return {"status": "oom", "memory_mb": e.value}
    except Exception as e:  # pylint: disable=broad-except
        return {"status": "error", "message": str(e)}


def main():
    parser = argparse.ArgumentParser(
        description="Run lps2lts on every .lps file in a directory"
    )
    parser.add_argument("mcrl2_path", help="Path to the directory containing the lps2lts binary")
    parser.add_argument("lps_dir", help="Directory to search for .lps files")
    parser.add_argument("--output", "-o", default="results.ndjson", help="Output NDJSON file (default: results.ndjson)")
    parser.add_argument("--max-threads", type=int, default=os.cpu_count() or 1,
                        help="Maximum thread count (powers of 2 up to this value, default: cpu count)")
    args = parser.parse_args()

    lps2lts = os.path.join(args.mcrl2_path, "lps2lts")
    lps_files = sorted(Path(args.lps_dir).rglob("*.lps"))

    if not lps_files:
        print(f"No .lps files found in {args.lps_dir}", file=sys.stderr)
        sys.exit(1)

    threads = thread_counts(args.max_threads)
    total = len(lps_files) * len(threads) * len(CACHE_CONFIGS) * RUNS_PER_CONFIG
    done = 0

    with open(args.output, "w", encoding="utf-8") as out:
        for lps_file in lps_files:
            name = str(lps_file.relative_to(args.lps_dir))

            for t in threads:
                for cache in CACHE_CONFIGS:
                    flags = [f"--threads={t}"] + cache["flags"]

                    for run_idx in range(RUNS_PER_CONFIG):
                        done += 1
                        print(f"[{done}/{total}] {name}  t{t}_{cache['name']}  run {run_idx + 1}/{RUNS_PER_CONFIG} ...", flush=True)
                        result = run_config(lps2lts, str(lps_file), flags)

                        if result["status"] == "ok":
                            print(f"  {result['time_s']:.2f}s  {result['memory_mb']:.1f}MB")
                        elif result["status"] == "timeout":
                            print(f"  timeout after {result['time_s']:.2f}s")
                        elif result["status"] == "oom":
                            print(f"  OOM at {result['memory_mb']:.1f}MB")
                        else:
                            print(f"  error: {result.get('message')}")
                        if result["status"] == "error" and "ToolNotFoundError" in result.get("message", ""):
                            print(f"Tool not found: {lps2lts}", file=sys.stderr)
                            sys.exit(1)

                        record = {
                            "file": name,
                            "threads": t,
                            "cached": "--cached" in cache["flags"],
                            "global_cache": "--global-cache" in cache["flags"],
                            "run": run_idx + 1,
                            **result,
                        }
                        out.write(json.dumps(record) + "\n")
                        out.flush()

    print(f"\nResults written to {args.output}")


if __name__ == "__main__":
    main()
