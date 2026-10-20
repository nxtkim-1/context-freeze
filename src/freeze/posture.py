"""Posture-based fatigue proxy from pose landmarks (not a medical measurement)."""

from __future__ import annotations

from dataclasses import dataclass
from math import atan2, degrees
from statistics import mean
from typing import Optional

Point = tuple[float, float]

# Neck forward travel (degrees past baseline) that counts as a full slump.
SLUMP_SATURATION_DEGREES = 25.0


@dataclass
class PoseFrame:
    """One frame's landmarks in normalized image coords; any may be missing."""

    left_ear: Optional[Point]
    right_ear: Optional[Point]
    left_shoulder: Optional[Point]
    right_shoulder: Optional[Point]


@dataclass
class Baseline:
    neck: float
    shoulder: float


def _midpoint(a: Optional[Point], b: Optional[Point]) -> Optional[Point]:
    if a is None or b is None:
        return None
    return ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)


def neck_angle(frame: PoseFrame) -> Optional[float]:
    """Angle in degrees of the ear-to-shoulder line away from vertical."""
    ear = _midpoint(frame.left_ear, frame.right_ear)
    shoulder = _midpoint(frame.left_shoulder, frame.right_shoulder)
    if ear is None or shoulder is None:
        return None
    dx = ear[0] - shoulder[0]
    dy = ear[1] - shoulder[1]
    return degrees(atan2(abs(dx), abs(dy)))


def shoulder_angle(frame: PoseFrame) -> Optional[float]:
    """Angle in degrees of the shoulder line away from horizontal."""
    left, right = frame.left_shoulder, frame.right_shoulder
    if left is None or right is None:
        return None
    dx = right[0] - left[0]
    dy = right[1] - left[1]
    return degrees(atan2(abs(dy), abs(dx)))


def calibrate(frames) -> Baseline:
    """Mean neck and shoulder angles over the upright calibration frames."""
    necks, shoulders = [], []
    for frame in frames:
        neck = neck_angle(frame)
        shoulder = shoulder_angle(frame)
        if neck is None or shoulder is None:
            continue
        necks.append(neck)
        shoulders.append(shoulder)
    if not necks:
        raise ValueError("calibration needs at least one frame with all landmarks")
    return Baseline(neck=mean(necks), shoulder=mean(shoulders))


def slump_score(frame: PoseFrame, baseline: Baseline) -> Optional[float]:
    """How far neck has moved forward past baseline, in [0, 1] (None if landmark missing)."""
    neck = neck_angle(frame)
    if neck is None:
        return None
    forward = neck - baseline.neck
    return max(0.0, min(1.0, forward / SLUMP_SATURATION_DEGREES))
