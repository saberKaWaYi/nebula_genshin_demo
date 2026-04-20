#!/bin/bash
set -e

CRON_SOURCE="/app/crawler/crontab.txt"
CRON_TARGET="/etc/cron.d/genshin-cron"

cp "$CRON_SOURCE" "$CRON_TARGET"
chmod 0644 "$CRON_TARGET"

mkdir -p /var/log
touch /var/log/cron.log

service cron start

echo "cron started, loading jobs from $CRON_TARGET"
exec tail -f /var/log/cron.log