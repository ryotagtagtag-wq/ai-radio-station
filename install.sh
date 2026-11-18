#!/usr/bin/env bash
#
# ai-radio-station Installer (Phase 0)
# Installs uv, Python, edge-tts, and initializes SQLite DB.
# Designed for shared rental servers (no root).
#

set -euo pipefail

INSTALL_DIR="$(cd "$(dirname "$0")" && pwd)"
echo "Install directory: $INSTALL_DIR"

# --------------------------------------------------------
# 1. Check curl/wget
# --------------------------------------------------------
if command -v curl >/dev/null 2>&1; then
  DOWNLOAD_CMD="curl -LsSf"
elif command -v wget >/dev/null 2>&1; then
  DOWNLOAD_CMD="wget -qO-"
else
  echo "ERROR: Neither curl nor wget is available." >&2
  exit 1
fi

# --------------------------------------------------------
# 2. Install uv (user-local, no root required)
# --------------------------------------------------------
if ! command -v uv >/dev/null 2>&1; then
  echo "Installing uv..."
  $DOWNLOAD_CMD https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
else
  echo "uv is already installed: $(which uv)"
fi

# --------------------------------------------------------
# 3. Install Python via uv
# --------------------------------------------------------
echo "Installing Python 3.11 via uv..."
uv python install 3.11

# --------------------------------------------------------
# 4. Install edge-tts via uv pip
# --------------------------------------------------------
echo "Installing edge-tts via uv..."
uv pip install edge-tts

# --------------------------------------------------------
# 5. Verify edge-tts
# --------------------------------------------------------
echo "Verifying edge-tts..."
uv run edge-tts --version || echo "WARNING: edge-tts verification failed (may still work)"

# --------------------------------------------------------
# 6. Initialize SQLite DB
# --------------------------------------------------------
DB_DIR="$INSTALL_DIR/db"
mkdir -p "$DB_DIR"
if [ ! -f "$DB_DIR/station.sqlite" ]; then
  echo "Initializing SQLite database..."
  php -r "
    \$db = new SQLite3('$DB_DIR/station.sqlite');
    \$db->exec('CREATE TABLE IF NOT EXISTS channels (id TEXT PRIMARY KEY, name TEXT, description TEXT, rss_url TEXT, tts_voice TEXT, tts_rate TEXT, tts_pitch TEXT, interval_type TEXT, interval_value INTEGER, jingle_start TEXT, jingle_end TEXT, template TEXT, last_run INTEGER, created_at INTEGER)');
    \$db->exec('CREATE TABLE IF NOT EXISTS episodes (id INTEGER PRIMARY KEY AUTOINCREMENT, channel_id TEXT, title TEXT, filename TEXT, duration INTEGER, pub_date INTEGER, created_at INTEGER)');
    \$db->exec('CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)');
    \$db->close();
    echo 'DB initialized.' . PHP_EOL;
  "
else
  echo "Database already exists."
fi

# --------------------------------------------------------
# 7. Config file
# --------------------------------------------------------
if [ ! -f "$INSTALL_DIR/config/config.php" ]; then
  if [ -f "$INSTALL_DIR/config.example.php" ]; then
    cp "$INSTALL_DIR/config.example.php" "$INSTALL_DIR/config/config.php"
    echo "Copied config.example.php -> config/config.php (please edit it)"
  fi
else
  echo "config/config.php already exists."
fi

# --------------------------------------------------------
# 8. Permissions
# --------------------------------------------------------
chmod 707 "$DB_DIR" 2>/dev/null || true
chmod 707 "$INSTALL_DIR/tmp" 2>/dev/null || true
chmod 707 "$INSTALL_DIR/public/audio" 2>/dev/null || true
chmod 707 "$INSTALL_DIR/public/feeds" 2>/dev/null || true

echo ""
echo "=== Installation complete ==="
echo "Next steps:"
echo "  1. Edit config/config.php with your settings"
echo "  2. Set up cron: crontab -e"
echo "     Example: */30 * * * * $INSTALL_DIR/cron/station_cron.sh"
echo "  3. Access public/admin/ in your browser to manage channels"
