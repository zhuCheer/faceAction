"""features 层单元测试：EAR / MAR / 位姿 / 移动方向计算。"""
import math
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.constants import (
    LEFT_EYE_IDX,
    RIGHT_EYE_IDX,
    MOUTH_TOP,
    MOUTH_BOTTOM,
    MOUTH_LEFT,
    MOUTH_RIGHT,
    NOSE_TIP,
    LEFT_CHEEK,
    RIGHT_CHEEK,
)
from core.features import (
    eye_aspect_ratio,
    mouth_aspect_ratio,
    head_pose,
    head_roll,
    head_move_direction,
    extract_features,
)


def _ellipse(lm, cx, cy, rx, ry, idxs):
    for k, idx in enumerate(idxs):
        ang = 2 * math.pi * k / len(idxs)
        lm[idx] = (cx + rx * math.cos(ang), cy + ry * math.sin(ang))


def make_landmarks(eye_ry=5, mouth_open=False, nose_dx=0.0, nose_dy=0.0):
    lm = {i: (100.0, 100.0) for i in range(500)}
    _ellipse(lm, 50, 50, 10, eye_ry, LEFT_EYE_IDX)
    _ellipse(lm, 150, 50, 10, eye_ry, RIGHT_EYE_IDX)
    if mouth_open:
        lm[MOUTH_TOP] = (110, 80)
        lm[MOUTH_BOTTOM] = (110, 110)
    else:
        lm[MOUTH_TOP] = (110, 94)
        lm[MOUTH_BOTTOM] = (110, 96)
    lm[MOUTH_LEFT] = (90, 95)
    lm[MOUTH_RIGHT] = (130, 95)
    lm[LEFT_CHEEK] = (30, 100)
    lm[RIGHT_CHEEK] = (170, 100)
    lm[NOSE_TIP] = (100 + nose_dx, 100 + nose_dy)
    return lm


class TestGeometry(unittest.TestCase):
    def test_ear_open_vs_closed(self):
        ear_open = eye_aspect_ratio(make_landmarks(eye_ry=5), LEFT_EYE_IDX)
        ear_closed = eye_aspect_ratio(make_landmarks(eye_ry=1), LEFT_EYE_IDX)
        self.assertGreater(ear_open, 0.3)
        self.assertLess(ear_closed, 0.15)

    def test_mar_open_vs_closed(self):
        mar_open = mouth_aspect_ratio(make_landmarks(mouth_open=True))
        mar_closed = mouth_aspect_ratio(make_landmarks(mouth_open=False))
        self.assertGreater(mar_open, 0.4)
        self.assertLess(mar_closed, 0.2)

    def test_head_pose_direction(self):
        shape = (200, 200, 3)
        _, yaw0 = head_pose(make_landmarks(), shape)
        self.assertLess(abs(yaw0), 0.05)
        _, yaw_r = head_pose(make_landmarks(nose_dx=40), shape)
        self.assertGreater(yaw_r, 0.1)
        pitch_d, _ = head_pose(make_landmarks(nose_dy=40), shape)
        self.assertGreater(pitch_d, 0.1)

    def test_head_roll_zero(self):
        self.assertLess(abs(head_roll(make_landmarks())), 1e-3)

    def test_head_move_direction(self):
        self.assertEqual(head_move_direction(0, 0.3, 0.12, 0.10), "move_right")
        self.assertEqual(head_move_direction(0, -0.3, 0.12, 0.10), "move_left")
        self.assertEqual(head_move_direction(0.2, 0, 0.12, 0.10), "move_down")
        self.assertEqual(head_move_direction(-0.2, 0, 0.12, 0.10), "move_up")
        self.assertEqual(head_move_direction(0, 0, 0.12, 0.10), "")

    def test_extract_features_shape(self):
        f = extract_features(make_landmarks(), (200, 200, 3))
        self.assertGreater(f.ear, 0.2)
        self.assertLess(f.mar, 0.2)


if __name__ == "__main__":
    unittest.main()