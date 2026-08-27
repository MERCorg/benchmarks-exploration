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
python3 /root/scripts/benchmark.py /root/mCRL2/build/stage/bin/ /root/input/ -max-threads=128 -o /root/results/lps2lts.ndjson

python3 /root/scripts/benchmark_variants.py /root/mCRL2-lps2lts/build/stage/bin/ /root/input --max-threads=128 -o /root/results_variants/lps2lts_variants.ndjson

python3 /root/scripts/benchmark.py /root/merc/target/release/ /root/input/ -o /root/results_merc/results.ndjson
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
	--output results_mcrl2/results.ndjson \
	--max-threads 128 
```

### `scripts/benchmark_merc.py`

Runs `merc-lps explore-explicit` on each `.lps` input and writes benchmark results to NDJSON.

- Tests caching variants: `none`, `local`.
- Optional: write generated state spaces (`.aut`) with `--aut-dir`.

```bash
python3 scripts/benchmark_merc.py <merc_bin_dir> <lps_dir> \
	--output results_merc/results.ndjson \
	--max-threads 128
```

### `scripts/create_plot_exploration.py`

A concrete instantiation of `create_plot.py` (the scatter-plot counterpart of
`scripts/create_table_exploration.py`). It compares two tools on the same metric
with one point per benchmark case, drawn against a dashed `y = x` reference line.

- Defaults to `merc-lps` (y-axis) vs `lps2lts` (x-axis) on single-thread time.
- Select the tools, metric, thread count and caching mode with `--y-tool`,
  `--x-tool`, `--metric`, `--threads` and `--caching`.

```bash
python3 scripts/create_plot_exploration.py

python3 scripts/create_plot_exploration.py \
	--y-tool merc-lps --x-tool lps2ltscf \
	--metric memory \
	-o scripts/exploration_scatter.tex
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