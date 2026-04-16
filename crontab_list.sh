#!/bin/bash
set -e

CRON_SOURCE="/app/crontab_task/crontab.txt"
CRON_TARGET="/etc/cron.d/genshin-cron"

cp "$CRON_SOURCE" "$CRON_TARGET"
chmod 0644 "$CRON_TARGET"

# 创建日志文件，避免 tail 失败
mkdir -p /var/log
touch /var/log/cron.log

service cron start

echo "cron started, loading jobs from $CRON_TARGET"
exec tail -f /var/log/cron.log
