#!/usr/bin/env python3

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "merc-py"))
from merc import RunProcess, TimeExceededError, MemoryExceededError, ToolNotFoundError  # type: ignore


def main():
    parser = argparse.ArgumentParser(
        description="Run lps2lts on every .lps.txt file in a directory"
    )
    parser.add_argument("mcrl2_path", help="Path to the directory containing the lps2lts binary")
    parser.add_argument("lps_dir", help="Directory to search for .lps.txt files")
    parser.add_argument("--output", "-o", default="results.json", help="Output JSON file (default: results.json)")
    args = parser.parse_args()

    lps2lts = os.path.join(args.mcrl2_path, "lps2lts")
    lps_files = sorted(Path(args.lps_dir).rglob("*.lps.txt"))

    if not lps_files:
        print(f"No .lps.txt files found in {args.lps_dir}", file=sys.stderr)
        sys.exit(1)

    results = {}
    for lps_file in lps_files:
        name = str(lps_file.relative_to(args.lps_dir))
        print(f"Running {name} ...", flush=True)
        try:
            proc = RunProcess(lps2lts, [str(lps_file)])
            results[name] = {
                "status": "ok",
                "time_s": proc.user_time,
                "memory_mb": proc.max_memory,
            }
            print(f"  {proc.user_time:.2f}s  {proc.max_memory:.1f}MB")
        except TimeExceededError as e:
            results[name] = {"status": "timeout", "time_s": e.value}
            print(f"  timeout after {e.value:.2f}s")
        except MemoryExceededError as e:
            results[name] = {"status": "oom", "memory_mb": e.value}
            print(f"  OOM at {e.value:.1f}MB")
        except ToolNotFoundError as e:
            print(f"Tool not found: {e}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:  # pylint: disable=broad-except
            results[name] = {"status": "error", "message": str(e)}
            print(f"  error: {e}")

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults written to {args.output}")


if __name__ == "__main__":
    main()
