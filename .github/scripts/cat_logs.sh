#!/bin/bash
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && cd ../.. && pwd)"

for file in ${PROJECT_DIR}/logs/log*
do
    echo $file
    cat $file
done