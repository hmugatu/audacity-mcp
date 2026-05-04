import pytest
from unittest.mock import MagicMock, call
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
        "Normalize: PeakLevel=-1.0 ApplyGain=True RemoveDcOffset=True StereoIndependent=False"
    )


def test_normalize_custom_peak():
    conn = make_conn()
    normalize(conn, peak_db=-3.0)
    conn.send_command.assert_called_once_with(
        "Normalize: PeakLevel=-3.0 ApplyGain=True RemoveDcOffset=True StereoIndependent=False"
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


def test_noise_reduction_profile_sends_profile_command():
    conn = make_conn()
    noise_reduction_profile(conn)
    conn.send_command.assert_called_once_with("NoiseReduction: ProfileOnly=True")


def test_noise_reduction_apply_sends_apply_command():
    conn = make_conn()
    noise_reduction_apply(conn)
    conn.send_command.assert_called_once_with(
        "NoiseReduction: Level=12 Sensitivity=6.0 Frequency=3"
    )


def test_noise_reduction_apply_custom_params():
    conn = make_conn()
    noise_reduction_apply(conn, level=6, sensitivity=3.0, frequency=2)
    conn.send_command.assert_called_once_with(
        "NoiseReduction: Level=6 Sensitivity=3.0 Frequency=2"
    )


def test_apply_macro_sends_macro_command():
    conn = make_conn()
    apply_macro(conn, "CleanPodcast")
    conn.send_command.assert_called_once_with("Macro_CleanPodcast:")
