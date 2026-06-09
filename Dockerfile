FROM ubuntu:26.04

# Install dependencies
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y \
# Dependencies for mCRL2
 build-essential \
 cmake \
 git \
 libboost-dev \
 python3 \
 python3-pip \
 python3-psutil \ 
 python3-venv \
 z3 \
# Requires to install Rust
 curl
 
# Build the mcrl22lps and lps2lts tools of mCRL2 from source
COPY ./mCRL2 /root/mCRL2/

# Configure build
RUN mkdir ~/mCRL2/build && cd ~/mCRL2/build && cmake . \
 -DCMAKE_BUILD_TYPE=RELEASE \
 -DMCRL2_ENABLE_GUI_TOOLS=OFF \
 ~/mCRL2

ARG THREADS=8
RUN cd ~/mCRL2/build && make -j${THREADS} lps2lts txt2lps

# Install Rust for building merc
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y

# Build merc-vpg from source
COPY ./merc /root/merc/

ARG THREADS=8
ENV PATH="/root/.cargo/bin:${PATH}"
RUN cd ~/merc/tools/mcrl2 \
    && cargo build --release -j${THREADS} --bin merc-lps

# Install merc-py module, and create a virtual environment
COPY merc-py /root/merc-py/

RUN python3 -m venv /root/.venv && /root/.venv/bin/pip install /root/merc-py

# Copy the experiments into the container
COPY ./cases /root/cases/
COPY ./scripts /root/scripts/

# Prepare the examples
RUN python3 /root/scripts/prepare.py /root/mCRL2/build/stage/bin/ /root/cases/