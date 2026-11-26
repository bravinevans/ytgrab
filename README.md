# ytgrab

A lightweight desktop app for downloading YouTube videos, playlists, and auto-generated mixes with `yt-dlp`. Built with Python and PyQt6 for Arch and Arch-based Linux distros.

## What It Does
- **Batch queue:** Paste one link or twenty (one per line). `ytgrab` works through them in order and tracks both overall queue progress and individual track percentages.
- **Smart link handling:** Automatically tells standard playlists, single videos, and `RD` YouTube Mixes apart. For `RD` mixes, it rewrites the broken `/playlist?list=RD...` URL into the `/watch?v=...&list=RD...` format YouTube actually serves.
- **Clean audio extraction:** Downloads only the audio stream when you pick MP3, M4A, or FLAC—no leftover `.webp` thumbnails cluttering your music folders unless you explicitly turn cover art on.
- **Fewer 403 blocks:** Spaces out requests during bulk pulls, keeps a local archive of finished tracks so interrupted runs pick up where they left off, and lets you pass cookies from Brave, Firefox, Chromium, Chrome, Vivaldi, or Edge.

## Installation

### Option 1: One-command install from GitHub Releases (Recommended)
Install the prebuilt Arch package directly with `pacman`:

```bash
sudo pacman -U [https://github.com/bravinevans/ytgrab/releases/download/v0.4.0/ytgrab-0.4.0-1-any.pkg.tar.zst](https://github.com/bravinevans/ytgrab/releases/download/v0.4.0/ytgrab-0.4.0-1-any.pkg.tar.zst)
```

### Option 2: Build from source with `makepkg`
Clone the repo and let `makepkg` pull the dependencies (`python-pyqt6`, `yt-dlp`, and `ffmpeg`) and register the desktop launcher:

```bash
git clone [https://github.com/bravinevans/ytgrab.git](https://github.com/bravinevans/ytgrab.git)
cd ytgrab
makepkg -si
```

Once installed, open **ytgrab** from your application menu or run `ytgrab` in any terminal.

### Option 3: Run without installing
If you already have `python-pyqt6`, `yt-dlp`, and `ffmpeg` installed, you can run the script directly:

```bash
sudo pacman -S --needed python-pyqt6 yt-dlp ffmpeg
git clone [https://github.com/bravinevans/ytgrab.git](https://github.com/bravinevans/ytgrab.git)
cd ytgrab
python3 ytgrab.py
```

## Updating & Uninstalling
Remove `ytgrab` anytime via `pacman`:

```bash
sudo pacman -Rns ytgrab
```

Download history is stored in `~/.local/share/ytgrab/archive.txt`. Delete that file if you want to re-download tracks you already grabbed earlier.
