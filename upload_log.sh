#!/bin/bash
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_NAME="${PROJECT_DIR}/logs/log_"$*""

cd ${PROJECT_DIR}
git pull
cp ~/Logs_accounts.txt ${LOG_NAME};
git add ${LOG_NAME}
git commit -m "[log]"$*""
git push

bash scripts/upgrade_browser.sh