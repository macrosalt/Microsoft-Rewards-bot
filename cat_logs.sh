#!/bin/bash
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

for file in ${PROJECT_DIR}/logs/log*
do
    cat $file
done