"""
effects.py — Audio effect and processing tools.

Noise reduction requires two steps:
  1. Select a noise-only region, call noise_reduction_profile(conn)
  2. Select the full audio, call noise_reduction_apply(conn)
"""

import logging

logger = logging.getLogger(__name__)


def normalize(conn, peak_db: float = -1.0) -> None:
    """Normalize the selection to `peak_db` dBFS (default -1.0)."""
    conn.send_command(
        f"Normalize: PeakLevel={peak_db} ApplyGain=True "
        f"RemoveDcOffset=True StereoIndependent=False"
    )
    logger.info("Normalized to %.1f dBFS", peak_db)


def amplify(conn, db: float) -> None:
    """Amplify the selection by `db` decibels."""
    ratio = 10 ** (db / 20)
    conn.send_command(f"Amplify: Ratio={ratio:.4f} AllowClipping=False")
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
    """
    conn.send_command("NoiseReduction: ProfileOnly=True")
    logger.info("Noise profile captured from current selection.")


def noise_reduction_apply(
    conn,
    level: int = 12,
    sensitivity: float = 6.00,
    frequency: int = 3,
) -> None:
    """Step 2 of noise reduction: apply the captured profile to the current selection."""
    conn.send_command(
        f"NoiseReduction: Level={level} Sensitivity={sensitivity} Frequency={frequency}"
    )
    logger.info("Applied noise reduction (level=%d, sensitivity=%.2f)", level, sensitivity)


def apply_macro(conn, macro_name: str) -> None:
    """Run a saved Audacity macro by name (Tools → Macros in Audacity)."""
    conn.send_command(f"Macro_{macro_name}:")
    logger.info("Applied macro: %s", macro_name)
