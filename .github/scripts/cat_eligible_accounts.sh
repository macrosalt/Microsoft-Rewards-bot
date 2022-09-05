#!/bin/bash
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && cd ../.. && pwd)"

for file in ${PROJECT_DIR}/logs/log*
do
    cat $file | \
    python3 ${PROJECT_DIR}/.github/scripts/eligible_accounts.py
done