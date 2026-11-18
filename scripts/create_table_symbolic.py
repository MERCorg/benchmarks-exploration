#!/usr/bin/env python3
"""Summarise the results of benchmark_symbolic.py as a Markdown table.

One row per input file, tool and strategy, one column per thread count, with the
median wall-clock time of the successful runs ("timeout", "oom" or "error" when no run
succeeded), and the best speedup over one thread. The number of states reported by
every run is read from its stdout/stderr dump; inputs on which two runs disagree are
listed after the table, so that a wrong result never goes unnoticed.
"""

import argparse
import json
import re
import statistics
import sys
from collections import defaultdict
from pathlib import Path

STATE_PATTERNS = [
    re.compile(r"number of states = ([0-9.e+]+)"),   # lpsreach
    re.compile(r"Number of states: ([0-9,]+)"),       # merc-lps
]


def states_of(record: dict) -> int | None:
    """The number of states printed by the run, if any."""
    for key in ("stdout", "stderr"):
        path = record.get(key)
        if not path or not Path(path).exists():
            continue
        text = Path(path).read_text(encoding="utf-8", errors="replace")
        for pattern in STATE_PATTERNS:
            matches = pattern.findall(text)
            if matches:
                return int(float(matches[-1].replace(",", "")))
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarise benchmark_symbolic.py results")
    parser.add_argument("inputs", nargs="+", type=Path, help="NDJSON result files")
    parser.add_argument("--output", "-o", type=Path, help="Markdown file (default: stdout)")
    args = parser.parse_args()

    times: dict[tuple, list[float]] = defaultdict(list)
    failures: dict[tuple, str] = {}
    states: dict[str, dict[int, list[str]]] = defaultdict(lambda: defaultdict(list))
    thread_set: set[int] = set()

    for path in args.inputs:
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            key = (record["name"], record["tool"], record["strategy"])
            threads = int(record["threads"])
            thread_set.add(threads)
            if record.get("status") == "ok":
                times[key + (threads,)].append(float(record["time_s"]))
                count = states_of(record)
                if count is not None:
                    states[record["name"]][count].append(f"{record['tool']} {record['strategy']} t{threads}")
            else:
                failures.setdefault(key + (threads,), record.get("status", "error"))

    threads = sorted(thread_set)
    rows = sorted({key[:3] for key in list(times) + list(failures)})

    out = ["| model | tool | strategy | " + " | ".join(f"t{t}" for t in threads) + " | best speedup |",
           "|---|---|---|" + "---:|" * len(threads) + "---:|"]
    for name, tool, strategy in rows:
        cells = []
        medians = {}
        for t in threads:
            values = times.get((name, tool, strategy, t))
            if values:
                medians[t] = statistics.median(values)
                cells.append(f"{medians[t]:.2f}")
            else:
                cells.append(failures.get((name, tool, strategy, t), "-"))
        speedup = f"{medians[1] / min(medians.values()):.2f}×" if 1 in medians else "-"
        out.append(f"| {Path(name).stem} | {tool} | {strategy} | " + " | ".join(cells) + f" | {speedup} |")

    disagreements = {name: counts for name, counts in states.items() if len(counts) > 1}
    if disagreements:
        out.append("")
        out.append("State counts that disagree:")
        for name, counts in sorted(disagreements.items()):
            for count, runs in sorted(counts.items()):
                out.append(f"- {name}: {count} states in {', '.join(sorted(set(runs)))}")

    text = "\n".join(out) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    if disagreements:
        sys.exit(1)


if __name__ == "__main__":
    main()
