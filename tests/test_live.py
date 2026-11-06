"""
Live tests against a running Audacity 3.x. Opt-in:

    AUDACITY_LIVE=1 uv run pytest tests/test_live.py -v

Open an *empty* project first. The tests refuse to run if it has tracks,
because they create and then remove tracks. Noise reduction is not covered:
its profile/reduce state lives inside Audacity and can't be reset by script.
"""

import os
import wave

import pytest

from audacity_mcp.client import AudacityConnection
from audacity_mcp.tools import effects, export, labels, tracks

pytestmark = pytest.mark.skipif(
    os.environ.get("AUDACITY_LIVE") != "1",
    reason="live Audacity tests are opt-in: set AUDACITY_LIVE=1",
)


@pytest.fixture
def conn():
    c = AudacityConnection(timeout=60)
    try:
        c.connect()
    except ConnectionError as exc:
        pytest.skip(str(exc))
    if tracks.get_tracks(c):
        c.disconnect()
        pytest.fail("Open an empty Audacity project before running live tests.")
    yield c
    if tracks.get_tracks(c):
        export.select_whole_project(c)
        c.send_command("RemoveTracks:")
    c.disconnect()


def make_noise(conn, seconds=4.0, amplitude=0.3):
    conn.send_command("NewMonoTrack:")
    n = len(tracks.get_tracks(conn))
    conn.send_command(f"SelectTracks: Track={n - 1} TrackCount=1 Mode=Set")
    tracks.select_time(conn, 0, seconds)
    conn.send_command(f"Noise: Type=White Amplitude={amplitude}")


def wav_info(path):
    with wave.open(str(path)) as w:
        frames = w.readframes(w.getnframes())
        width = w.getsampwidth()
        samples = [
            int.from_bytes(frames[i:i + width], "little", signed=True)
            for i in range(0, len(frames), width)
        ]
        peak = max(abs(s) for s in samples) / (1 << (8 * width - 1))
        return {"seconds": w.getnframes() / w.getframerate(),
                "channels": w.getnchannels(), "peak": peak}


def test_get_tracks_and_selection(conn):
    make_noise(conn)
    assert [t["kind"] for t in tracks.get_tracks(conn)] == ["wave"]
    tracks.select_time(conn, 1, 2)
    sel = tracks.get_selection(conn)
    assert (sel["Start"], sel["End"]) == (1, 2)


def test_normalize_sets_peak(conn, tmp_path):
    make_noise(conn)
    effects.normalize(conn, peak_db=-6.0)
    out = tmp_path / "norm.wav"
    export.export_selection(conn, str(out), channels=1)
    assert wav_info(out)["peak"] == pytest.approx(0.501, abs=0.01)


def test_export_audio_with_spaces_and_after_add_label(conn, tmp_path):
    """Regression: a freshly added label swallowed SelectAll, cutting the export short."""
    make_noise(conn, seconds=4.0)
    labels.add_label(conn, time=1.0, text="mark")
    tracks.select_time(conn, 0, 1)
    out = tmp_path / "my mix" / "full song.wav"
    out.parent.mkdir()
    export.export_audio(conn, str(out))
    info = wav_info(out)
    assert info["seconds"] == pytest.approx(4.0)
    assert info["channels"] == 2


def test_export_selection_exports_only_selection(conn, tmp_path):
    make_noise(conn)
    tracks.select_time(conn, 0.5, 1.5)
    out = tmp_path / "part.wav"
    export.export_selection(conn, str(out), channels=1)
    assert wav_info(out)["seconds"] == pytest.approx(1.0)


def test_labels_round_trip_and_export(conn, tmp_path):
    make_noise(conn)
    labels.add_label(conn, time=3.0, text="outro")
    labels.add_label(conn, time=1.0, end=2.0, text='the "drop"')
    got = [(l["start"], l["end"], l["text"]) for l in labels.get_labels(conn)]
    assert got == [(1, 2, 'the "drop"'), (3, 3, "outro")]

    out = tmp_path / "labels.txt"
    assert labels.export_labels(conn, str(out)) == 2
    assert out.read_text().splitlines()[0] == '1.000000\t2.000000\tthe "drop"'


def test_import_audio(conn, tmp_path):
    make_noise(conn, seconds=1.0)
    src = tmp_path / "a take.wav"
    export.export_audio(conn, str(src))
    export.import_audio(conn, str(src))
    assert [t["name"] for t in tracks.get_tracks(conn)][-1] == "a take"
