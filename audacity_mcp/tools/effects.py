"""
effects.py — Audio effect and processing tools.

Effect boolean parameters must be sent as 1/0: Audacity 3.x silently ignores
"True"/"False" and falls back to the default.

Noise reduction requires two steps:
  1. Select a noise-only region, call noise_reduction_profile(conn)
  2. Select the full audio, call noise_reduction_apply(conn)

Scripted NoiseReduction takes no parameters. Whether a call captures a
profile or reduces noise depends on hidden state inside Audacity: the first
call in an Audacity session profiles, and every later call reduces, using the
settings last chosen in the Noise Reduction dialog
(libraries/lib-builtin-effects/NoiseReductionBase.cpp). Only the dialog's
"Get Noise Profile" button captures a new profile. The functions below refuse
calls that would do the opposite of what they say.
"""

import logging

logger = logging.getLogger(__name__)

# Whether noise_reduction_profile has run since this server started. It
# can't see profiles captured in Audacity's dialog or survive a restart of
# either program, but it catches the common misuse.
_noise_profile_captured = False


def normalize(conn, peak_db: float = -1.0) -> None:
    """Normalize the selection to `peak_db` dBFS (default -1.0)."""
    conn.send_command(
        f"Normalize: PeakLevel={peak_db} ApplyVolume=1 "
        f"RemoveDcOffset=1 StereoIndependent=0"
    )
    logger.info("Normalized to %.1f dBFS", peak_db)


def amplify(conn, db: float) -> None:
    """Amplify the selection by `db` decibels."""
    ratio = 10 ** (db / 20)
    conn.send_command(f"Amplify: Ratio={ratio:.4f} AllowClipping=0")
    logger.info("Amplified by %.1f dB (ratio %.4f)", db, ratio)


def fade_in(conn) -> None:
    """Apply a linear fade-in over the current selection."""
    conn.send_command("FadeIn:")


def fade_out(conn) -> None:
    """Apply a linear fade-out over the current selection."""
    conn.send_command("FadeOut:")


def noise_reduction_profile(conn) -> None:
    """
    Step 1 of noise reduction: capture a noise profile.
    Before calling this, select a region of pure background noise using select_time().

    Works once per Audacity session. A second scripted call would *reduce*
    noise in the selection instead, so it is refused; capture a new profile
    with Effect → Noise Reduction → Get Noise Profile in Audacity.
    """
    global _noise_profile_captured
    if _noise_profile_captured:
        raise RuntimeError(
            "A noise profile was already captured in this session. Audacity "
            "3.x can only capture one over scripting; calling NoiseReduction "
            "again would reduce noise instead. To re-profile, select the noise "
            "in Audacity and use Effect → Noise Reduction → Get Noise Profile, "
            "then call noise_reduction_apply."
        )
    conn.send_command("NoiseReduction:")
    _noise_profile_captured = True
    logger.info("Noise profile captured from current selection.")


def noise_reduction_apply(conn, level=None, sensitivity=None, frequency=None) -> None:
    """
    Step 2 of noise reduction: apply the captured profile to the current selection.

    Uses the reduction settings last chosen in Audacity's Noise Reduction
    dialog. Audacity ignores scripted values, so `level`, `sensitivity` and
    `frequency` are accepted only for backward compatibility.
    """
    if not _noise_profile_captured:
        raise RuntimeError(
            "No noise profile captured yet: call noise_reduction_profile on a "
            "noise-only selection first. Without one, Audacity would capture a "
            "profile from this selection instead of reducing noise."
        )
    if (level, sensitivity, frequency) != (None, None, None):
        logger.warning("Ignoring level/sensitivity/frequency: Audacity doesn't "
                       "accept them when scripted; set them in the dialog.")
    conn.send_command("NoiseReduction:")
    logger.info("Applied noise reduction.")


def apply_macro(conn, macro_name: str) -> None:
    """Run a saved Audacity macro by name (Tools → Macros in Audacity)."""
    conn.send_command(f"Macro_{macro_name}:")
    logger.info("Applied macro: %s", macro_name)
