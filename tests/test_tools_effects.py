import pytest
from unittest.mock import MagicMock, call
from audacity_mcp.tools import effects as effects_module
from audacity_mcp.tools.effects import (
    normalize, amplify, fade_in, fade_out,
    noise_reduction_profile, noise_reduction_apply, apply_macro,
)


def make_conn() -> MagicMock:
    conn = MagicMock()
    conn.send_command.return_value = "BatchCommand finished: OK"
    return conn


def test_normalize_default_peak():
    conn = make_conn()
    normalize(conn)
    conn.send_command.assert_called_once_with(
        "Normalize: PeakLevel=-1.0 ApplyVolume=1 RemoveDcOffset=1 StereoIndependent=0"
    )


def test_normalize_custom_peak():
    conn = make_conn()
    normalize(conn, peak_db=-3.0)
    conn.send_command.assert_called_once_with(
        "Normalize: PeakLevel=-3.0 ApplyVolume=1 RemoveDcOffset=1 StereoIndependent=0"
    )


def test_amplify_sends_ratio():
    conn = make_conn()
    amplify(conn, db=6.0)
    cmd = conn.send_command.call_args[0][0]
    assert cmd.startswith("Amplify: Ratio=")
    ratio = float(cmd.split("Ratio=")[1].split()[0])
    assert abs(ratio - 1.9953) < 0.001


def test_fade_in_sends_command():
    conn = make_conn()
    fade_in(conn)
    conn.send_command.assert_called_once_with("FadeIn:")


def test_fade_out_sends_command():
    conn = make_conn()
    fade_out(conn)
    conn.send_command.assert_called_once_with("FadeOut:")


@pytest.fixture(autouse=True)
def reset_noise_profile_state(monkeypatch):
    monkeypatch.setattr(effects_module, "_noise_profile_captured", False)


def test_amplify_disallows_clipping_with_numeric_bool():
    conn = make_conn()
    amplify(conn, db=3.0)
    assert conn.send_command.call_args[0][0].endswith("AllowClipping=0")


def test_noise_reduction_profile_sends_bare_command():
    """Scripted NoiseReduction takes no parameters; the first call profiles."""
    conn = make_conn()
    noise_reduction_profile(conn)
    conn.send_command.assert_called_once_with("NoiseReduction:")


def test_noise_reduction_profile_twice_is_refused():
    """A second scripted call would reduce noise instead of profiling."""
    conn = make_conn()
    noise_reduction_profile(conn)
    with pytest.raises(RuntimeError, match="Get Noise Profile"):
        noise_reduction_profile(conn)
    assert conn.send_command.call_count == 1


def test_noise_reduction_apply_after_profile_sends_bare_command():
    conn = make_conn()
    noise_reduction_profile(conn)
    noise_reduction_apply(conn)
    assert conn.send_command.call_args_list == [call("NoiseReduction:"), call("NoiseReduction:")]


def test_noise_reduction_apply_without_profile_is_refused():
    """Without a profile, Audacity would profile the selection instead."""
    conn = make_conn()
    with pytest.raises(RuntimeError, match="noise_reduction_profile"):
        noise_reduction_apply(conn)
    conn.send_command.assert_not_called()


def test_noise_reduction_apply_ignores_legacy_params():
    conn = make_conn()
    noise_reduction_profile(conn)
    noise_reduction_apply(conn, level=6, sensitivity=3.0, frequency=2)
    conn.send_command.assert_called_with("NoiseReduction:")


def test_apply_macro_sends_macro_command():
    conn = make_conn()
    apply_macro(conn, "CleanPodcast")
    conn.send_command.assert_called_once_with("Macro_CleanPodcast:")
