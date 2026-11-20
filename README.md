# Cascabel

A Qt-based desktop music player: it plays your local library, pulls songs
from YouTube, and keeps Spotify playlists in sync — all in one queue-driven,
touch-friendly interface.

## What it does

- **Library and playlists** — songs live in a portable SQLite database
  (`music.db`); playlists can be created and imported, the queue can be
  sorted and searched, and tracks show cover art and fetched metadata.
- **YouTube** — search and stream straight from YouTube with a local stream
  cache, or download songs into the library. Browser cookies can be reused
  to get past YouTube's "confirm you're not a bot" wall.
- **Spotify sync** — link a Spotify playlist once; Cascabel imports it and
  re-checks it on every start, adding new songs automatically. Bring your
  own free Spotify API (Client ID + Secret from developer.spotify.com):
  enter it in Settings, or right in the Link Spotify window — with no API
  saved, all Spotify features simply stay off.
- **Failed downloads** — imports that fail are tracked per playlist and can
  be retried in one click from the Failed Songs dialog (or with
  `retry_failed.py` from a terminal).
- **Playback** — shuffle, seek, volume, an equalizer-style visualizer, and a
  fullscreen now-playing view with big cover art, a tap-anywhere EQ progress
  bar, and an idle mode. While fullscreen is active, the screen is kept
  awake.
- **Touch mode** — big buttons and a wedge-shaped volume bar sized for a
  touch panel: swipe a queue entry right to play it next, swipe it left to
  drop it from the queue. The Cascabel logo is the play/pause artwork.
- **Desktop integration** — media keys and media widgets work even when the
  app is not focused (MPRIS on Linux, native media keys on Windows).
- **Network sync** — two Cascabel instances on the same network can play in
  sync; play, pause and seek are mirrored both ways.
- **Remotes** — HDMI-CEC support for Raspberry Pi installs (control playback
  with the TV remote) and MOCUTE-052 gamepad support via raw input.

## Installing (Linux)

Everything is handled by one script:

```bash
bash '(re)installthewholegodamnthingffs.sh'
```

It works from an existing checkout and on a fresh machine alike:

- installs any missing system packages (git, python3 + venv, pip, ffmpeg and
  the Qt runtime libraries) via apt, dnf, pacman or zypper,
- clones the repository to `~/Music/Cascabel` if it is not already there
  (otherwise it just pulls the latest changes),
- creates a `.venv` with the pinned Python dependencies,
- builds the app with PyInstaller,
- installs it to `~/.local/opt/Cascabel`,
- pre-renders the taskbar / menu icon and creates the application-menu entry,
- moves an old "Music Engine" library to the new location, if one exists.

Re-run the same script any time to update to the latest version and rebuild.
After it finishes, start Cascabel from the application menu, or run
`~/.local/opt/Cascabel` directly.

Optional overrides:

```bash
REPO_URL=<url> BRANCH=<branch> bash '(re)installthewholegodamnthingffs.sh'
```

Note for atomic distros (Bazzite / Silverblue style): system packages
installed by the script apply after a reboot.

Windows: the app itself runs on Windows (bundled ffmpeg, native media keys),
but the install script is Linux-only.

## Running from source

```bash
source .venv/bin/activate
python3 main.py
```

This uses the same virtual environment and dependencies the install script
sets up.

## Where the data lives

- Run from a checkout: the project folder itself (`music.db`, `playlists/`).
- Installed app: `~/.local/share/cascabel`.

To move a library between machines, copy `music.db` and the `playlists`
folder into that data folder — all stored paths are portable.

