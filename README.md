# ytgrab

A minimalist PyQt6 desktop GUI for `yt-dlp` built for Arch and Arch-based Linux distributions.

## Features
- **Multi-URL Batch Queue:** Paste single or multiple links (one per line) and process them sequentially.
- **Per-URL Auto-Detection:** Automatically distinguishes single videos, standard playlists, and YouTube `RD` Auto-Mixes (rewriting `list=RD...` URLs to their seed `/watch?v=...` form).
- **Anti-403 Resilience:** Built-in request pacing (`--sleep-interval`), download deduplication archive, optional browser cookie extraction, and automatic cleanup of orphaned thumbnail files.
- **Multiple Formats:** MP3 (V0), M4A, FLAC, 1080p MP4, and Best MKV.

## Installation (Arch / Arch-based)
```bash
git clone https://github.com/bravinevans/ytgrab.git
cd ytgrab
makepkg -si
```
