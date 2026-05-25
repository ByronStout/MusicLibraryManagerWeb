import pytest
from unittest.mock import MagicMock, patch

from app import app, PAGE_SIZE


# ---------------------------------------------------------------------------
# Fixtures & helpers
# ---------------------------------------------------------------------------

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def make_yt(playlists=None, tracks=None, history=None):
    mock = MagicMock()
    mock.get_library_playlists.return_value = playlists or []
    mock.get_playlist.return_value = {"tracks": tracks or []}
    mock.get_history.return_value = history or []
    return mock


def make_track(n):
    return {
        "videoId": f"video_{n}",
        "setVideoId": f"set_{n}",
        "title": f"Track {n}",
        "artists": [{"name": "Artist"}],
        "album": {"name": "Album"},
        "duration": "3:00",
    }


PLAYLIST = {"playlistId": "PL123", "title": "My Playlist"}


# ---------------------------------------------------------------------------
# GET /
# ---------------------------------------------------------------------------

class TestIndex:
    def test_returns_200(self, client):
        with patch("app.load_ytmusic", return_value=make_yt(playlists=[PLAYLIST])):
            resp = client.get("/")
        assert resp.status_code == 200

    def test_shows_playlist_title(self, client):
        with patch("app.load_ytmusic", return_value=make_yt(playlists=[PLAYLIST])):
            resp = client.get("/")
        assert b"My Playlist" in resp.data

    def test_ytmusic_error_renders_page_with_error(self, client):
        with patch("app.load_ytmusic", side_effect=FileNotFoundError("browser.json not found")):
            resp = client.get("/")
        assert resp.status_code == 200
        assert b"browser.json not found" in resp.data


# ---------------------------------------------------------------------------
# GET /playlist/<playlist_id>
# ---------------------------------------------------------------------------

class TestPlaylistView:
    def test_returns_200(self, client):
        yt = make_yt(playlists=[PLAYLIST], tracks=[make_track(1)])
        with patch("app.load_ytmusic", return_value=yt):
            resp = client.get("/playlist/PL123")
        assert resp.status_code == 200

    def test_shows_track_title(self, client):
        yt = make_yt(playlists=[PLAYLIST], tracks=[make_track(1)])
        with patch("app.load_ytmusic", return_value=yt):
            resp = client.get("/playlist/PL123")
        assert b"Track 1" in resp.data

    def test_unknown_playlist_returns_404(self, client):
        yt = make_yt(playlists=[PLAYLIST])
        with patch("app.load_ytmusic", return_value=yt):
            resp = client.get("/playlist/UNKNOWN")
        assert resp.status_code == 404

    def test_empty_playlist_renders_without_error(self, client):
        yt = make_yt(playlists=[PLAYLIST], tracks=[])
        with patch("app.load_ytmusic", return_value=yt):
            resp = client.get("/playlist/PL123")
        assert resp.status_code == 200

    def test_history_lookup_shown_in_page(self, client):
        track = make_track(1)
        history = [{"videoId": "video_1", "played": "Yesterday"}]
        yt = make_yt(playlists=[PLAYLIST], tracks=[track], history=history)
        with patch("app.load_ytmusic", return_value=yt):
            resp = client.get("/playlist/PL123")
        assert b"Yesterday" in resp.data

    # --- Pagination ---

    def test_page_1_shows_first_track_not_overflow(self, client):
        tracks = [make_track(i) for i in range(PAGE_SIZE + 5)]
        yt = make_yt(playlists=[PLAYLIST], tracks=tracks)
        with patch("app.load_ytmusic", return_value=yt):
            resp = client.get("/playlist/PL123?page=1")
        assert b"Track 0" in resp.data
        assert f"Track {PAGE_SIZE}".encode() not in resp.data

    def test_page_2_shows_overflow_not_first_track(self, client):
        tracks = [make_track(i) for i in range(PAGE_SIZE + 5)]
        yt = make_yt(playlists=[PLAYLIST], tracks=tracks)
        with patch("app.load_ytmusic", return_value=yt):
            resp = client.get("/playlist/PL123?page=2")
        assert f"Track {PAGE_SIZE}".encode() in resp.data
        assert b"Track 0" not in resp.data

    def test_page_beyond_total_clamped_to_last(self, client):
        tracks = [make_track(i) for i in range(5)]
        yt = make_yt(playlists=[PLAYLIST], tracks=tracks)
        with patch("app.load_ytmusic", return_value=yt):
            resp = client.get("/playlist/PL123?page=999")
        assert resp.status_code == 200
        assert b"Track 0" in resp.data

    def test_page_below_1_clamped_to_1(self, client):
        tracks = [make_track(i) for i in range(5)]
        yt = make_yt(playlists=[PLAYLIST], tracks=tracks)
        with patch("app.load_ytmusic", return_value=yt):
            resp = client.get("/playlist/PL123?page=0")
        assert resp.status_code == 200
        assert b"Track 0" in resp.data

    def test_total_pages_ceiling_division(self, client):
        # PAGE_SIZE + 1 tracks should produce 2 pages, not 1
        tracks = [make_track(i) for i in range(PAGE_SIZE + 1)]
        yt = make_yt(playlists=[PLAYLIST], tracks=tracks)
        with patch("app.load_ytmusic", return_value=yt):
            resp = client.get("/playlist/PL123?page=2")
        assert f"Track {PAGE_SIZE}".encode() in resp.data

    def test_exactly_page_size_tracks_is_one_page(self, client):
        tracks = [make_track(i) for i in range(PAGE_SIZE)]
        yt = make_yt(playlists=[PLAYLIST], tracks=tracks)
        with patch("app.load_ytmusic", return_value=yt):
            resp = client.get("/playlist/PL123?page=2")
        # Clamped back to page 1
        assert b"Track 0" in resp.data


# ---------------------------------------------------------------------------
# GET /api/playlists
# ---------------------------------------------------------------------------

class TestApiPlaylists:
    def test_returns_json_list(self, client):
        with patch("app.load_ytmusic", return_value=make_yt(playlists=[PLAYLIST])):
            resp = client.get("/api/playlists")
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, list)
        assert data[0] == {"playlistId": "PL123", "title": "My Playlist"}

    def test_only_exposes_id_and_title(self, client):
        full = {**PLAYLIST, "count": 42, "thumbnails": []}
        with patch("app.load_ytmusic", return_value=make_yt(playlists=[full])):
            resp = client.get("/api/playlists")
        item = resp.get_json()[0]
        assert set(item.keys()) == {"playlistId", "title"}

    def test_ytmusic_error_returns_500(self, client):
        with patch("app.load_ytmusic", side_effect=Exception("auth failed")):
            resp = client.get("/api/playlists")
        assert resp.status_code == 500
        assert resp.get_json()["error"] == "auth failed"


# ---------------------------------------------------------------------------
# POST /playlist/<id>/add_tracks
# ---------------------------------------------------------------------------

class TestAddTracks:
    def test_success_calls_api_and_returns_200(self, client):
        yt = make_yt()
        with patch("app.load_ytmusic", return_value=yt):
            resp = client.post("/playlist/PL123/add_tracks", json={"videoIds": ["v1", "v2"]})
        assert resp.status_code == 200
        assert resp.get_json()["success"] is True
        yt.add_playlist_items.assert_called_once_with("PL123", videoIds=["v1", "v2"])

    def test_empty_video_ids_returns_400(self, client):
        with patch("app.load_ytmusic", return_value=make_yt()):
            resp = client.post("/playlist/PL123/add_tracks", json={"videoIds": []})
        assert resp.status_code == 400
        assert "error" in resp.get_json()

    def test_missing_video_ids_key_returns_400(self, client):
        with patch("app.load_ytmusic", return_value=make_yt()):
            resp = client.post("/playlist/PL123/add_tracks", json={})
        assert resp.status_code == 400

    def test_ytmusic_error_returns_500(self, client):
        yt = make_yt()
        yt.add_playlist_items.side_effect = Exception("quota exceeded")
        with patch("app.load_ytmusic", return_value=yt):
            resp = client.post("/playlist/PL123/add_tracks", json={"videoIds": ["v1"]})
        assert resp.status_code == 500
        assert resp.get_json()["error"] == "quota exceeded"


# ---------------------------------------------------------------------------
# POST /playlist/<id>/delete
# ---------------------------------------------------------------------------

class TestDeleteTracks:
    TRACK = {"videoId": "v1", "setVideoId": "s1"}

    def test_success_calls_api_and_returns_200(self, client):
        yt = make_yt()
        with patch("app.load_ytmusic", return_value=yt):
            resp = client.post("/playlist/PL123/delete", json={"tracks": [self.TRACK]})
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["deleted"] == 1
        yt.remove_playlist_items.assert_called_once_with("PL123", [self.TRACK])

    def test_deleted_count_matches_input(self, client):
        tracks = [{"videoId": f"v{i}", "setVideoId": f"s{i}"} for i in range(5)]
        with patch("app.load_ytmusic", return_value=make_yt()):
            resp = client.post("/playlist/PL123/delete", json={"tracks": tracks})
        assert resp.get_json()["deleted"] == 5

    def test_empty_tracks_returns_400(self, client):
        with patch("app.load_ytmusic", return_value=make_yt()):
            resp = client.post("/playlist/PL123/delete", json={"tracks": []})
        assert resp.status_code == 400
        assert "error" in resp.get_json()

    def test_missing_tracks_key_returns_400(self, client):
        with patch("app.load_ytmusic", return_value=make_yt()):
            resp = client.post("/playlist/PL123/delete", json={})
        assert resp.status_code == 400

    def test_ytmusic_error_returns_500(self, client):
        yt = make_yt()
        yt.remove_playlist_items.side_effect = Exception("network error")
        with patch("app.load_ytmusic", return_value=yt):
            resp = client.post("/playlist/PL123/delete", json={"tracks": [self.TRACK]})
        assert resp.status_code == 500
        assert resp.get_json()["error"] == "network error"
