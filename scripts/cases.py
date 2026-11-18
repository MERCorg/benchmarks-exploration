"""Helpers to collect the benchmark cases.

The cases directory contains the shared cases at the top-level, and two
subdirectories `explicit/` and `symbolic/` with cases that are only suitable
for the explicit and symbolic benchmarks respectively.
"""

import sys
from pathlib import Path


def collect_lps_files(cases_dir: str, kind: str) -> list[Path]:
    """Returns the shared .lps files in cases_dir and those in cases_dir/kind, exits when none are found."""
    root = Path(cases_dir)
    lps_files = sorted(root.glob("*.lps")) + sorted((root / kind).rglob("*.lps"))

    if not lps_files:
        print(f"No .lps files found in {root} or {root / kind}", file=sys.stderr)
        sys.exit(1)

    names = [f.name for f in lps_files]
    duplicates = sorted({n for n in names if names.count(n) > 1})
    if duplicates:
        print(f"Duplicate case names in {root}: {', '.join(duplicates)}", file=sys.stderr)
        sys.exit(1)

    return lps_files
