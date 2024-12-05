FROM ubuntu:24.04

RUN apt-get update --yes && \
    apt-get install --yes --no-install-recommends \
    # Basic utilities
    sudo vim git curl jq pkg-config lsb-release wget software-properties-common gnupg \
    # SSL related dependencies
    openssl libssl-dev \
    # Build dependencies
    g++ ninja-build cmake gfortran build-essential \
    # Mathematical libraries
    libblas-dev libopenblas-dev liblapack-dev \
    # Compression library
    libz-dev \
    # LLVM dependencies
    clang-format clang-tidy clang-tools clang clangd libc++-dev libc++1 libc++abi-dev \
    libc++abi1 libclang-dev libclang1 liblldb-dev libllvm-ocaml-dev libomp-dev \
    libomp5 lld lldb llvm-dev llvm-runtime llvm python3-clang \
    libpolly-18-dev libzstd-dev \
    # Python interpreter and package managers 
    cargo python3 python3-pip python3-venv && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements-dev.txt .

RUN python3 -m venv venv && \
    venv/bin/python3 -m pip install --upgrade pip && \
    venv/bin/python3 -m pip install -r requirements-dev.txt
    # venv/bin/python3 -m pip install qbraid qbraid-qir[cirq,qasm3] qbraid-core[runner] && \
    # rm -rf $(venv/bin/python3 -m pip cache dir)
