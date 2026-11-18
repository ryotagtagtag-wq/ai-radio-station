# AI Radio Station

A completely free, 24/7 automated AI radio station system that runs on a single shared rental server (no root, SSH only, cron enabled).

## Features

- **Multi-channel**: Manage 3–5 independent radio channels with different themes and update frequencies
- **PWA (Progressive Web App)**: Smartphone-friendly UI, installable to home screen, offline playback support
- **Podcast RSS**: Each channel has its own RSS feed, subscribable via Apple Podcasts, Spotify, etc.
- **Free TTS**: edge-tts (via uv) for high-quality Japanese speech synthesis — no API keys required
- **Cron automation**: Fully automatic episode generation and distribution
- **Lightweight**: PHP + SQLite, no heavy local AI models, safe for shared hosting

## Requirements

- Shared rental server with SSH access
- PHP (7.4+)
- SQLite (PHP extension)
- cron
- `curl` or `wget`
- `uv` (installed by `install.sh` in user directory)

## Quick Start

```bash
# Clone the repository
git clone https://github.com/ryotagtagtag-wq/ai-radio-station.git
cd ai-radio-station

# Run the installer (installs uv, Python, edge-tts, initializes DB)
bash install.sh

# Copy config example and edit
cp config.example.php config/config.php
# Edit config/config.php with your settings

# Set up cron (example: every 30 minutes)
crontab -e
# */30 * * * * /path/to/ai-radio-station/cron/station_cron.sh
```

## Directory Structure

```
ai-radio-station/
├── install.sh              # One-shot installer (uv, edge-tts, DB)
├── config/config.php       # Site and channel settings
├── db/station.sqlite       # SQLite database (auto-created)
├── public/                 # Public HTML, PWA, audio, RSS
├── lib/                    # PHP libraries
├── cron/                   # Cron entrypoint scripts
├── tmp/                    # Temporary files and logs
├── templates/              # Script templates
├── jingles/                # Jingle MP3 files
└── run_station.php         # Main execution script
```

## License

MIT License
