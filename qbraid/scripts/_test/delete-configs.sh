#!/bin/bash

configs=(".qbraid/qbraidrc" ".qbraid/config" ".qiskit/qiskitrc" \
    ".aws/config" ".aws/credentials")

for item in ${configs[@]}; do
    rm -f $HOME/$item
done