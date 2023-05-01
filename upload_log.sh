#!/bin/bash
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_NAME="${PROJECT_DIR}/logs/log_"$*""

# push log
cd ${PROJECT_DIR}
git pull
cp ~/Logs_accounts.txt ${LOG_NAME};
git add ${LOG_NAME}
git commit -m "[log]"$*""
git push

# update browser, driver version
/bin/bash scripts/upgrade_browser.sh > browser.txt

# clean large size log
logfile=cron.log
filesize=$(stat -c %s "$logfile")

if [ "$filesize" -gt $((200 * 1024 * 1024)) ]; then
    echo "Log file is larger than 200MB, deleting..."
    rm "$logfile"
fi