try:
    from flask import Flask, render_template, abort, url_for, request, jsonify
    from werkzeug.exceptions import HTTPException
except ImportError as exc:
    raise ImportError(
        "Flask is required to run this application. Install it with 'pip install Flask'"
    ) from exc

import os

from ytmusicapi import YTMusic

AUTH_FILE = "browser.json"

app = Flask(__name__)

_ytmusic = None


def load_ytmusic():
    global _ytmusic
    if _ytmusic is None:
        if not os.path.exists(AUTH_FILE):
            raise FileNotFoundError(
                f"Authentication file '{AUTH_FILE}' not found. Copy your browser.json file into this project folder."
            )
        _ytmusic = YTMusic(AUTH_FILE)
    return _ytmusic


@app.route("/")
def index():
    error = None
    playlists = []
    try:
        ytmusic = load_ytmusic()
        playlists = ytmusic.get_library_playlists()
    except Exception as exc:
        error = str(exc)
    return render_template("index.html", playlists=playlists, error=error)


PAGE_SIZE = 50


@app.route("/playlist/<playlist_id>")
def playlist_view(playlist_id):
    error = None
    playlist = None
    tracks = []
    history_lookup = {}
    total_pages = 1
    try:
        page = max(1, request.args.get("page", 1, type=int))
        ytmusic = load_ytmusic()
        playlists = ytmusic.get_library_playlists()
        playlist = next((p for p in playlists if p["playlistId"] == playlist_id), None)
        if playlist is None:
            abort(404)
        results = ytmusic.get_playlist(playlist_id, limit=None)
        all_tracks = results.get("tracks", [])
        total_pages = max(1, -(-len(all_tracks) // PAGE_SIZE))  # ceiling division
        page = min(page, total_pages)
        tracks = all_tracks[(page - 1) * PAGE_SIZE : page * PAGE_SIZE]
        history = ytmusic.get_history()
        history_lookup = {t["videoId"]: t.get("played", "Never") for t in history}
    except HTTPException:
        raise
    except Exception as exc:
        error = str(exc)
    return render_template(
        "playlist.html",
        playlist=playlist,
        tracks=tracks,
        history_lookup=history_lookup,
        error=error,
        page=page,
        total_pages=total_pages,
        playlist_id=playlist_id,
    )


@app.route("/api/playlists")
def api_playlists():
    try:
        ytmusic = load_ytmusic()
        playlists = ytmusic.get_library_playlists()
        return jsonify([{"playlistId": p["playlistId"], "title": p["title"]} for p in playlists])
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/playlist/<playlist_id>/add_tracks", methods=["POST"])
def playlist_add_tracks(playlist_id):
    try:
        data = request.get_json()
        video_ids = data.get("videoIds", [])
        if not video_ids:
            return jsonify({"error": "No tracks specified"}), 400
        ytmusic = load_ytmusic()
        ytmusic.add_playlist_items(playlist_id, videoIds=video_ids)
        return jsonify({"success": True})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/playlist/<playlist_id>/delete", methods=["POST"])
def playlist_delete_tracks(playlist_id):
    try:
        data = request.get_json()
        tracks = data.get("tracks", [])
        if not tracks:
            return jsonify({"error": "No tracks specified"}), 400
        ytmusic = load_ytmusic()
        ytmusic.remove_playlist_items(playlist_id, tracks)
        return jsonify({"success": True, "deleted": len(tracks)})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.errorhandler(404)
def not_found(error):
    return render_template("index.html", playlists=[], error="Playlist not found."), 404


if __name__ == "__main__":
    app.run(debug=True)
