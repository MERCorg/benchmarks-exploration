#!/usr/bin/env python3

import argparse
import os
import subprocess
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description="Run txt2lps on every .lps.txt file in a directory"
    )
    parser.add_argument("mcrl2_path", help="Path to the directory containing the txt2lps binary")
    parser.add_argument("lps_dir", help="Directory to search for .lps.txt files")
    args = parser.parse_args()

    txt2lps = os.path.join(args.mcrl2_path, "txt2lps")
    lps_files = sorted(Path(args.lps_dir).rglob("*.lps.txt"))

    if not lps_files:
        print(f"No .lps.txt files found in {args.lps_dir}", file=sys.stderr)
        sys.exit(1)

    tmp_dir = Path("input")
    tmp_dir.mkdir(exist_ok=True)

    for lps_file in lps_files:
        out_file = tmp_dir / lps_file.with_suffix("").name  # strip .txt -> .lps
        print(f"  {lps_file} -> {out_file}", flush=True)
        subprocess.run([txt2lps, str(lps_file), str(out_file)], check=True)


if __name__ == "__main__":
    main()
