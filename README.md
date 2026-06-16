# Overview

This repository contains a setup to benchmark the state space exploration algorithms of mCRL2 and merc. The inputs are various specifications derived from the mCRL2 example directory.

First of all, the third-party repositories are included as git submodules. To initialize them, run the following command:

```bash
git submodule update --init --recursive
```

The docker image builds the tools and prepares the input textual specifications for the benchmarks. To build the docker image, run the following command:

```bash
docker build -t benchmarks-exploration .
```

Then we can perform the actual benchmarks from within the docker container. To start the container, run the following command:

```bash
docker run -it --rm benchmarks-exploration
```

The benchmarking script is located at `scripts/benchmark.py`. To run the benchmarks, execute the following command from within the container:

```bash
python3 scripts/benchmark.py /root/mCRL2/build/stage/bin /root/input/
```

## Scripts

This repository contains three top-level scripts in `scripts/` and helper utilities in `merc-py/merc/`.

### `scripts/prepare.py`

Converts all `.lps.txt` models to `.lps` models using `txt2lps`.

```bash
python3 scripts/prepare.py <mcrl2_bin_dir> <cases_dir>
```

### `scripts/benchmark.py`

Runs `lps2lts` on each `.lps` input and writes benchmark results to NDJSON.

- Tests caching variants: `none`, `local`.
- Tests thread counts: powers of two up to `--max-threads`.
- Optional: write generated state spaces (`.aut`) with `--aut-dir`.

```bash
python3 scripts/benchmark.py <mcrl2_bin_dir> <lps_dir> \
	--output results.ndjson \
	--max-threads 8 \
	--aut-dir aut
```

### `scripts/benchmark_merc.py`

Runs `merc-lps explore-explicit` on each `.lps` input and writes benchmark results to NDJSON.

- Tests caching variants: `none`, `local`, `global`.
- Optional: write generated state spaces (`.aut`) with `--aut-dir`.

```bash
python3 scripts/benchmark_merc.py <merc_bin_dir> <lps_dir> \
	--output results_merc.ndjson \
	--max-threads 8 \
	--aut-dir aut_merc
```

### `merc-py/merc/create_table.py`

Generates a LaTeX table from JSON or NDJSON benchmark output.

- With one input file, it keeps the old summary behavior.
- With multiple input files, it merges rows by benchmark name plus the selected merge keys.
- Each input contributes a `Time (s)` and `Memory (MB)` column for side-by-side comparison.

```bash
python3 merc-py/merc/create_table.py results.ndjson

python3 merc-py/merc/create_table.py results-a.ndjson results-b.ndjson \
	--merge-key threads \
	--merge-key caching \
	--label baseline \
	--label optimized \
	-o comparison.tex
```

### `merc-py/merc/benchmarks.py`

Shared benchmarking engine used by both benchmark scripts.

- Executes runs sequentially or in parallel.
- Supports timeout and memory limits.
- Stores per-run stdout/stderr dumps.
- Appends one NDJSON record per run and can resume from an existing output file.

## Verifying the results

To verify the results, you can compare the generated `.aut` files from both `lps2lts` and `merc-lps explore-explicit` for the same input `.lps` file. They can be produced by passing `--aut-dir` to the respective benchmark scripts.

```bash