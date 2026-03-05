#!/usr/bin/env sh

# Created by: Vladislav Punko <iam.vlad.punko@gmail.com>
# Created date: 2021-06-16

set -o errexit

if [ -z "$1" ]; then
  # Show all active python kernels on the working notebook server on the current machine.
  notebook-environments --show | sort --reverse --ignore-case | nl
else
  notebook-environments "$@"
fi
