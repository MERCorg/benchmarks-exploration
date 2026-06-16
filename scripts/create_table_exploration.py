"""Generate the benchmarks-exploration per-experiment table.

This is a concrete instantiation of the generic table interface in
``create_table.py``. It produces a (very wide) table with one row per
experiment name and caching mode, and columns grouped first by metric, then by
tool, then by thread count:

    Name        Caching | Time (s)                       | Memory (MB)
                        | lps2lts ... merc-lps  (1..128)  | lps2lts ... merc-lps (1..128)
    --------------------+--------------------------------+------------------------------
    1394-fin    none    |  ...                           |  ...
    1394-fin    local   |  ...                           |  ...
    ...

The ``merc-lps`` results have no thread dimension, so they only populate the
single-thread column; every other thread count renders as ``\\na``.
"""

import argparse
import sys
from pathlib import Path

# Import the generic table module directly (without triggering the merc package
# __init__, which pulls in heavyweight runtime dependencies such as psutil).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "merc-py" / "merc"))

from create_table import (  # noqa: E402  (path is set up above)
    AGGREGATORS,
    Column,
    Row,
    build_table,
    load_records,
    render_latex_table,
)

REPO_ROOT = Path(__file__).resolve().parent.parent

# Row order (tool, caching). Each tool is shown once per caching mode.
TOOL_ORDER = ["lps2lts", "lps2lts_variant", "lps2ltspr", "lps2ltscf", "merc-lps"]
CACHING_MODES = ["none", "local"]
THREAD_COUNTS = [1, 2, 4, 8, 16, 32, 64, 128]

DEFAULT_BASE = REPO_ROOT / "results" / "lps2lts.ndjson"
DEFAULT_VARIANTS = REPO_ROOT / "results_variants" / "lps2lts_variants.ndjson"
DEFAULT_MERC = REPO_ROOT / "results_merc" / "results.ndjson"
DEFAULT_OUTPUT = REPO_ROOT / "scripts" / "exploration_scalability.tex"


def load_tagged(base: Path, variants: Path, merc: Path) -> list[dict]:
    """Load the three result sources and tag every record with a ``_tool`` name."""
    records: list[dict] = []

    for record in load_records(base):
        tagged = dict(record)
        tagged["_tool"] = "lps2lts"
        records.append(tagged)

    for record in load_records(variants):
        tagged = dict(record)
        tool = record.get("tool")
        # The variant build of lps2lts is distinguished from the base build.
        tagged["_tool"] = "lps2lts_variant" if tool == "lps2lts" else tool
        # lps2ltspr performs --project, which always implies caching, so its
        # runs are local caching regardless of how they were recorded. The
        # "none" caching row therefore stays empty (a dash) for this tool.
        if tool == "lps2ltspr":
            tagged["caching"] = "local"
        records.append(tagged)

    for record in load_records(merc):
        tagged = dict(record)
        tagged["_tool"] = "merc-lps"
        # merc-lps has no thread dimension; treat it as the single-thread result.
        tagged["threads"] = 1
        records.append(tagged)

    return records


def experiment_names(records: list[dict]) -> list[str]:
    """Return the sorted set of experiment names across all sources."""
    return sorted({record.get("name", "unknown") for record in records})


def make_rows(records: list[dict]) -> list[Row]:
    rows: list[Row] = []
    for name in experiment_names(records):
        for caching in CACHING_MODES:
            rows.append(
                Row(
                    labels=(name, caching),
                    select=lambda record, name=name, caching=caching: (
                        record.get("name") == name and record.get("caching") == caching
                    ),
                )
            )
    return rows


def make_columns(thread_counts: list[int]) -> list[Column]:
    # With a single thread count there is no point repeating it for every
    # column, so the per-thread header level is dropped for readability.
    single = len(thread_counts) == 1
    columns: list[Column] = []
    for metric, group in (("time", "Time (s)"), ("memory", "Memory (MB)")):
        for tool in TOOL_ORDER:
            for threads in thread_counts:
                path = (group, tool) if single else (group, tool, str(threads))
                columns.append(
                    Column(
                        path=path,
                        select=lambda record, tool=tool, threads=threads: (
                            record.get("_tool") == tool
                            and int(record.get("threads", 1)) == threads
                        ),
                        metric=metric,
                    )
                )
    return columns


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate the benchmarks-exploration scalability LaTeX table."
    )
    parser.add_argument("--base", type=Path, default=DEFAULT_BASE,
                        help="NDJSON results for the base lps2lts build.")
    parser.add_argument("--variants", type=Path, default=DEFAULT_VARIANTS,
                        help="NDJSON results for the lps2lts/lps2ltspr/lps2ltscf variant builds.")
    parser.add_argument("--merc", type=Path, default=DEFAULT_MERC,
                        help="NDJSON results for merc-lps (single thread).")
    parser.add_argument("--aggregate", choices=sorted(AGGREGATORS), default="mean",
                        help="How to combine values across benchmark cases and runs.")
    parser.add_argument("--single-thread", dest="single_thread", action="store_true",
                        help="Only show the threads == 1 values for easy comparison.")
    parser.add_argument("--fragment", dest="standalone", action="store_false",
                        help="Emit only the tabular fragment instead of a standalone document.")
    parser.add_argument("--output", "-o", type=Path, default=DEFAULT_OUTPUT,
                        help="Path to the generated LaTeX table.")
    args = parser.parse_args()

    thread_counts = [1] if args.single_thread else THREAD_COUNTS
    records = load_tagged(args.base, args.variants, args.merc)
    rows = make_rows(records)
    columns = make_columns(thread_counts)
    table_rows = build_table(records, rows, columns, aggregate=AGGREGATORS[args.aggregate])

    # Bold the best (lowest) time and the best (lowest) memory in each row,
    # comparing across every tool and thread count within each metric group.
    render_latex_table(
        args.output,
        ["Name", "Caching"],
        columns,
        table_rows,
        compare_key=lambda column: column.path[0],
        standalone=args.standalone,
    )
    print(f"Table written to {args.output} (aggregate: {args.aggregate})")


if __name__ == "__main__":
    main()
