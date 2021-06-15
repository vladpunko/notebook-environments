#!/usr/bin/env sh

# Copyright 2020 (c) Vladislav Punko <iam.vlad.punko@gmail.com>

set -o errexit

if [ -z "$1" ]; then
  # Show all active python kernels on the working notebook server on the current machine.
  notebook-environments --show | sort --reverse --ignore-case | nl
else
  notebook-environments "$@"
fi
