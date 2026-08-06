#!/usr/bin/env bash
# Refresh live data + rebuild the static site. Run manually or via cron.
# crontab example (every 6h): 0 */6 * * * /opt/data/asicminerprices/refresh.sh >> /opt/data/asicminerprices/refresh.log 2>&1
set -e
cd "$(dirname "$0")"
python3 fetch_data.py && python3 build.py
echo "[$(date -Is)] refresh OK"
