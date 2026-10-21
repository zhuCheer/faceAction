"""detector 层单元测试：眨眼/单眼/张嘴/点头/方向化摇头/歪头。"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.detector import Detector, _deadzone
from core.features import Features


def F(ear=0.4, ear_left=None, ear_right=None, mar=0.1, pitch=0.0, yaw=0.0, roll=0.0):
    return Features(
        ear=ear,
        ear_left=ear if ear_left is None else ear_left,
        ear_right=ear if ear_right is None else ear_right,
        mar=mar, pitch=pitch, yaw=yaw, roll=roll,
    )


class TestBlink(unittest.TestCase):
    def test_single_blink(self):
        d = Detector()
        evs = []
        for _ in range(3):
            evs += d.feed(F(ear=0.1))
        evs += d.feed(F(ear=0.4))          # 释放 -> 记录 pending
        for _ in range(11):
            evs += d.feed(F(ear=0.4))
        self.assertIn("blink", evs)
        self.assertNotIn("double_blink", evs)

    def test_double_blink(self):
        d = Detector()
        evs = []
        for _ in range(3):
            evs += d.feed(F(ear=0.1))
        evs += d.feed(F(ear=0.4))
        for _ in range(3):
            evs += d.feed(F(ear=0.1))
        evs += d.feed(F(ear=0.4))
        self.assertIn("double_blink", evs)

    def test_long_blink(self):
        d = Detector()
        evs = []
        for _ in range(30):
            evs += d.feed(F(ear=0.1))
        evs += d.feed(F(ear=0.4))
        self.assertIn("long_blink", evs)


class TestWink(unittest.TestCase):
    def test_wink_left(self):
        d = Detector()
        evs = []
        for _ in range(3):
            evs += d.feed(F(ear=0.3, ear_left=0.1, ear_right=0.5))
        evs += d.feed(F(ear=0.4, ear_left=0.5, ear_right=0.5))
        self.assertIn("wink_left", evs)

    def test_wink_right(self):
        d = Detector()
        evs = []
        for _ in range(3):
            evs += d.feed(F(ear=0.3, ear_left=0.5, ear_right=0.1))
        evs += d.feed(F(ear=0.4, ear_left=0.5, ear_right=0.5))
        self.assertIn("wink_right", evs)


class TestMouth(unittest.TestCase):
    def test_mouth_open(self):
        d = Detector()
        evs = []
        for _ in range(3):
            evs += d.feed(F(mar=0.6))
        self.assertIn("mouth_open", evs)
        self.assertTrue(d.is_mouth_open)

    def test_mouth_close(self):
        d = Detector()
        evs = []
        for _ in range(3):
            evs += d.feed(F(mar=0.6))
        for _ in range(30):
            evs += d.feed(F(mar=0.1))
        self.assertIn("mouth_close", evs)
        self.assertFalse(d.is_mouth_open)


class TestHeadGesture(unittest.TestCase):
    def test_nod(self):
        d = Detector()
        pitches = [0.0, 0.1, 0.2, 0.2, 0.2, 0.2, 0.1, 0.0]
        evs = []
        for p in pitches:
            evs += d.feed(F(pitch=p))
        self.assertIn("nod", evs)

    def test_nod_up(self):
        d = Detector()
        pitches = [0.0, -0.1, -0.2, -0.2, -0.2, -0.2, -0.1, 0.0]
        evs = []
        for p in pitches:
            evs += d.feed(F(pitch=p))
        self.assertIn("nod_up", evs)
        self.assertNotIn("nod", evs)

    def test_shake_left(self):
        d = Detector()
        yaws = [0.0, 0.1, 0.3, 0.3, 0.3, 0.3, 0.1, 0.0]
        evs = []
        for y in yaws:
            evs += d.feed(F(yaw=y))
        self.assertIn("shake_left", evs)

    def test_shake_right(self):
        d = Detector()
        yaws = [0.0, -0.1, -0.3, -0.3, -0.3, -0.3, -0.1, 0.0]
        evs = []
        for y in yaws:
            evs += d.feed(F(yaw=y))
        self.assertIn("shake_right", evs)

    def test_tilt(self):
        d = Detector()
        evs = []
        for _ in range(5):
            evs += d.feed(F(roll=0.3))
        self.assertIn("tilt_right", evs)


class TestDeadzone(unittest.TestCase):
    def test_deadzone(self):
        self.assertEqual(_deadzone(0.05, 0.12), 0.0)
        self.assertAlmostEqual(_deadzone(0.2, 0.12), 0.08)
        self.assertAlmostEqual(_deadzone(-0.2, 0.12), -0.08)


if __name__ == "__main__":
    unittest.main()