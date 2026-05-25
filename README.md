# MusicLibraryManager Web

A browser-based interface for browsing YouTube Music playlists and track history using `ytmusicapi`.

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
3. Copy `browser.json` from your existing CLI project into this folder.

## Run

```powershell
python app.py
```

Then open `http://127.0.0.1:5000` in your browser.
