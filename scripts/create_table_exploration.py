"""Generate the benchmarks-exploration per-experiment table.

This is a concrete instantiation of the generic table interface in
``create_table.py``. It produces a table with one row per experiment name and,
for each metric, one column per (caching, control-flow) combination:

    Name      | Time (s)                        | Memory (MB)
              | none        | local             | none        | local
              | cf   no-cf  | cf   no-cf        | cf   no-cf  | cf   no-cf
    ----------+---------------------------... --+--------------------------...
    1394-fin  |  ...                            |  ...
    ...
"""

import argparse
import sys
from pathlib import Path

from merc import (
    AGGREGATORS,
    Column,
    Row,
    create_table,
)

REPO_ROOT = Path(__file__).resolve().parent.parent

# Column dimensions: caching mode and whether control-flow analysis is on.
CACHING_MODES = ["none", "local"]
CONTROL_FLOW = [(True, "cf"), (False, "no-cf")]

DEFAULT_OUTPUT = REPO_ROOT / "scripts" / "exploration_scalability.tex"

def experiment_names(records: list[dict]) -> list[str]:
    """Return the sorted set of experiment names."""
    return sorted({record.get("name", "unknown") for record in records})


def make_rows(records: list[dict]) -> list[Row]:
    return [
        Row(
            labels=(name,),
            select=lambda record, name=name: record.get("name") == name,
        )
        for name in experiment_names(records)
    ]


def make_columns() -> list[Column]:
    columns: list[Column] = []
    for metric, group in (("time", "Time (s)"), ("memory", "Memory (MB)")):
        for caching in CACHING_MODES:
            for cf_value, cf_label in CONTROL_FLOW:
                columns.append(
                    Column(
                        path=(group, caching, cf_label),
                        select=lambda record, caching=caching, cf_value=cf_value: (
                            record.get("caching") == caching
                            and bool(record.get("control-flow")) == cf_value
                        ),
                        metric=metric,
                    )
                )
    return columns


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate the benchmarks-exploration LaTeX table."
    )
    parser.add_argument("--input-lps2lts", type=Path, required=True,
                        help="NDJSON results for lps2lts.")
    parser.add_argument("--input-merc", type=Path, required=True,
                        help="NDJSON results for merc-lps.")
    parser.add_argument("--aggregate", choices=sorted(AGGREGATORS), default="mean",
                        help="How to combine values across benchmark cases and runs.")
    parser.add_argument("--fragment", dest="standalone", action="store_false",
                        help="Emit only the tabular fragment instead of a standalone document.")
    parser.add_argument("--output", "-o", type=Path, default=DEFAULT_OUTPUT,
                        help="Path to the generated LaTeX table.")
    args = parser.parse_args()

    create_table([args.input_lps2lts, args.input_merc], merge_keys=["caching", "threads", "control-flow"], labels=[ "lps2lts", "merc-lps"], output=str(args.output))


if __name__ == "__main__":
    main()
