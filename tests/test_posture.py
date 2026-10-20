import pytest

from freeze.posture import (
    SLUMP_SATURATION_DEGREES,
    Baseline,
    PoseFrame,
    calibrate,
    neck_angle,
    shoulder_angle,
    slump_score,
)


def upright_frame():
    # Ears directly above shoulders: neck vertical, shoulders level.
    return PoseFrame(
        left_ear=(0.4, 0.2),
        right_ear=(0.6, 0.2),
        left_shoulder=(0.4, 0.5),
        right_shoulder=(0.6, 0.5),
    )


def forward_frame():
    # Ear midpoint shifted sideways from the shoulders: neck off vertical.
    return PoseFrame(
        left_ear=(0.5, 0.2),
        right_ear=(0.7, 0.2),
        left_shoulder=(0.4, 0.5),
        right_shoulder=(0.6, 0.5),
    )


def test_upright_neck_is_vertical():
    assert neck_angle(upright_frame()) == pytest.approx(0.0)


def test_level_shoulders_are_horizontal():
    assert shoulder_angle(upright_frame()) == pytest.approx(0.0)


def test_upright_scores_zero_against_own_baseline():
    frame = upright_frame()
    baseline = calibrate([frame])
    assert slump_score(frame, baseline) == pytest.approx(0.0)


def test_forward_scores_higher_than_upright():
    baseline = calibrate([upright_frame()])
    assert slump_score(forward_frame(), baseline) > slump_score(upright_frame(), baseline)


def test_score_saturates_at_one():
    baseline = calibrate([upright_frame()])
    # Ears far to the side of the shoulders push well past saturation.
    extreme = PoseFrame(
        left_ear=(1.0, 0.4),
        right_ear=(1.2, 0.4),
        left_shoulder=(0.4, 0.5),
        right_shoulder=(0.6, 0.5),
    )
    assert slump_score(extreme, baseline) == 1.0


def test_score_stays_in_range():
    baseline = calibrate([upright_frame()])
    for frame in (upright_frame(), forward_frame()):
        score = slump_score(frame, baseline)
        assert 0.0 <= score <= 1.0


def test_baseline_averages_several_frames():
    baseline = calibrate([upright_frame(), forward_frame()])
    expected = (neck_angle(upright_frame()) + neck_angle(forward_frame())) / 2
    assert baseline.neck == pytest.approx(expected)


def test_missing_landmark_gives_none():
    frame = PoseFrame(
        left_ear=None,
        right_ear=(0.6, 0.2),
        left_shoulder=(0.4, 0.5),
        right_shoulder=(0.6, 0.5),
    )
    assert neck_angle(frame) is None
    assert slump_score(frame, Baseline(neck=0.0, shoulder=0.0)) is None


def test_calibration_without_frames_raises():
    with pytest.raises(ValueError):
        calibrate([])


def test_saturation_constant_is_reachable():
    # A move of exactly the saturation amount lands at a full score.
    baseline = Baseline(neck=0.0, shoulder=0.0)
    forward = PoseFrame(
        left_ear=(0.4, 0.2),
        right_ear=(0.6, 0.2),
        left_shoulder=(0.4, 0.5),
        right_shoulder=(0.6, 0.5),
    )
    at_saturation = Baseline(neck=neck_angle(forward) - SLUMP_SATURATION_DEGREES, shoulder=0.0)
    assert slump_score(forward, at_saturation) == pytest.approx(1.0)
