#!/usr/bin/env bash
#
# ai-radio-station cron entrypoint
# Prevents double execution with flock.
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
LOCK_FILE="$SCRIPT_DIR/tmp/station.lock"
LOG_FILE="$SCRIPT_DIR/tmp/logs/cron.log"

mkdir -p "$SCRIPT_DIR/tmp/logs"

# flock: if another process holds the lock, exit immediately (non-blocking)
exec 9>"$LOCK_FILE"
if ! flock -n 9; then
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] Another instance is running. Skipping." >> "$LOG_FILE"
  exit 0
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Cron started." >> "$LOG_FILE"

# Run the main PHP script
php "$SCRIPT_DIR/run_station.php" >> "$LOG_FILE" 2>&1

EXIT_CODE=$?
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Cron finished with exit code $EXIT_CODE." >> "$LOG_FILE"

exit $EXIT_CODE
