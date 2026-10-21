"""anti_peep 层单元测试：非对称防抖 (隐藏即时 / 恢复需稳定 800ms) 与隐藏状态。"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.anti_peep import AntiPeep

DEBOUNCE = 0.8


def make_ap(enabled=False, debounce=DEBOUNCE):
    ap = AntiPeep(restore_debounce_seconds=debounce)
    if enabled:
        ap.toggle()
    return ap


class TestAntiPeep(unittest.TestCase):
    def test_default_disabled(self):
        ap = make_ap()
        self.assertFalse(ap.enabled)
        # 关闭时人脸变化也不输出命令
        self.assertEqual(ap.on_face(False, True, 0.0), [])

    def test_toggle(self):
        ap = make_ap()
        ap.toggle()
        self.assertTrue(ap.enabled)
        ap.toggle()
        self.assertFalse(ap.enabled)

    def test_hide_immediate_when_watching(self):
        ap = make_ap(enabled=True)
        # 刷抖音时人脸离开 -> 立即最小化, 无防抖延时
        self.assertEqual(ap.on_face(False, True, 0.0), ["hide"])
        self.assertTrue(ap.hidden)

    def test_hide_ignored_when_not_watching(self):
        ap = make_ap(enabled=True)
        # 非刷抖音 (选择态) 人脸离开 -> 不触发最小化
        self.assertEqual(ap.on_face(False, False, 0.0), [])
        self.assertFalse(ap.hidden)

    def test_no_redundant_hide(self):
        ap = make_ap(enabled=True)
        self.assertEqual(ap.on_face(False, True, 0.0), ["hide"])
        # 已是最小化状态, 持续无人脸不重复触发
        self.assertEqual(ap.on_face(False, True, 1.0), [])
        self.assertEqual(ap.on_face(False, True, 2.0), [])

    def test_restore_requires_debounce(self):
        ap = make_ap(enabled=True)
        ap.on_face(False, True, 0.0)          # -> hide
        self.assertEqual(ap.on_face(True, True, 1.0), [])   # 人脸回归, 开始计时
        self.assertEqual(ap.on_face(True, True, 1.5), [])   # 未满 800ms
        self.assertEqual(ap.on_face(True, True, 1.8), ["restore"])  # 满 800ms -> restore
        self.assertFalse(ap.hidden)

    def test_restore_flicker_resets_debounce(self):
        ap = make_ap(enabled=True)
        ap.on_face(False, True, 0.0)          # -> hide
        ap.on_face(True, True, 1.0)           # 人脸回归, 开始计时
        ap.on_face(False, True, 1.5)          # 人脸消失, 重置计时 (波动)
        ap.on_face(True, True, 2.0)           # 再次回归, 重新计时 (从 2.0 开始)
        # 需要持续到 2.0 + 0.8 = 2.8 才能恢复 (使用 2.81 避免浮点精度边界)
        self.assertEqual(ap.on_face(True, True, 2.7), [])   # 2.7-2.0=0.7 < 0.8
        self.assertEqual(ap.on_face(True, True, 2.81), ["restore"])  # 2.81-2.0=0.81 -> restore

    def test_disabled_tracks_state_without_command(self):
        ap = make_ap()
        self.assertEqual(ap.on_face(False, True, 0.0), [])
        self.assertFalse(ap.face_present)
        self.assertFalse(ap.hidden)
        ap.toggle()
        # 开启后, 人脸回归 (但从未隐藏) -> 不输出恢复
        self.assertEqual(ap.on_face(True, True, 1.0), [])
        self.assertTrue(ap.face_present)


if __name__ == "__main__":
    unittest.main()