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
