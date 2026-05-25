# MusicLibraryManager Web

A browser-based interface for browsing and managing YouTube Music playlists using `ytmusicapi`.

## Features

- Browse all playlists in your YouTube Music library
- View paginated track listings with title, artist, album, duration, and last-played date
- Select individual tracks or all tracks on the current page via checkboxes
- **Copy** selected tracks to another playlist (with live progress bar)
- **Delete** selected tracks from the current playlist (with confirmation dialog)

## Requirements

- Python 3.9+
- A `browser.json` authentication file (see below)

## Setup

1. Create a Python virtual environment:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

2. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```

3. Generate `browser.json` for YouTube Music authentication:
   ```powershell
   ytmusicapi browser
   ```
   This will prompt you to paste request headers copied from your browser's DevTools
   (see the [ytmusicapi authentication docs](https://ytmusicapi.readthedocs.io/en/stable/setup/browser.html)
   for step-by-step instructions). Place the resulting `browser.json` in the project root.

## Run

```powershell
python app.py
```

Then open `http://127.0.0.1:5000` in your browser.
