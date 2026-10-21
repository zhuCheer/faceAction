"""state_machine 层单元测试：行为锚定 + 看抖音/防偷窥。"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.constants import BEHAVIORS, MODE_HINTS
from core.anti_peep import AntiPeep
from core.state_machine import BehaviorStateMachine
from i18n import set_language, t


def setUpModule():
    set_language("zh")


def tearDownModule():
    set_language("auto")


def make_sm(anti_peep=None):
    return BehaviorStateMachine(anti_peep)


class TestMenu(unittest.TestCase):
    def test_default_first_is_douyin(self):
        self.assertEqual(BEHAVIORS[0][0], "douyin")
        self.assertEqual(t(BEHAVIORS[0][1]), "看抖音")

    def test_two_items_only(self):
        self.assertEqual([mid for mid, _ in BEHAVIORS], ["douyin", "anti_peep"])

    def test_cycle_and_confirm_douyin(self):
        sm = make_sm()
        step = sm.update(["shake_right"], "", 0)
        self.assertTrue(step.is_menu)
        self.assertEqual(step.menu_index, 1)
        step = sm.update(["shake_left"], "", 1)
        self.assertEqual(step.menu_index, 0)
        step = sm.update(["nod"], "", 2)
        self.assertFalse(step.is_menu)
        self.assertEqual(step.mode, "douyin")

    def test_menu_hint_contains_confirm(self):
        sm = make_sm()
        step = sm.update([], "", 0)
        self.assertIn("点头确认", step.hint)


class TestAntiPeepToggle(unittest.TestCase):
    def test_nod_toggles_on_and_stays_in_menu(self):
        sm = make_sm()
        sm.update(["shake_right"], "", 0)         # index 1 = 防偷窥
        step = sm.update(["nod"], "", 1)
        self.assertTrue(step.is_menu)
        self.assertIsNone(step.mode)
        self.assertTrue(step.anti_peep)
        self.assertIn("已开启", step.bubble)

    def test_nod_toggles_off(self):
        sm = make_sm()
        sm.update(["shake_right"], "", 0)
        sm.update(["nod"], "", 1)
        step = sm.update(["nod"], "", 2)
        self.assertFalse(step.anti_peep)
        self.assertIn("已关闭", step.bubble)

    def test_external_anti_peep_object_used(self):
        ap = AntiPeep()
        sm = make_sm(ap)
        sm.update(["shake_right"], "", 0)
        sm.update(["nod"], "", 1)
        self.assertTrue(ap.enabled)


class TestDouyinMode(unittest.TestCase):
    def _enter_douyin(self, sm):
        return sm.update(["nod"], "", 0.0)

    def test_enter_opens_douyin(self):
        sm = make_sm()
        step = self._enter_douyin(sm)
        self.assertEqual(step.mode, "douyin")
        self.assertIn("open_douyin", [g[0] for g in step.gestures])

    def test_nod_next_video(self):
        sm = make_sm()
        self._enter_douyin(sm)
        step = sm.update(["nod"], "", 1.0)
        self.assertIn("nod", [g[0] for g in step.gestures])
        self.assertIn("下一个视频", step.bubble)

    def test_nod_up_prev_video(self):
        sm = make_sm()
        self._enter_douyin(sm)
        step = sm.update(["nod_up"], "", 1.0)
        self.assertIn("nod_up", [g[0] for g in step.gestures])
        self.assertIn("上一个视频", step.bubble)

    def test_double_blink_single_click(self):
        sm = make_sm()
        self._enter_douyin(sm)
        step = sm.update(["double_blink"], "", 1.0)
        self.assertIn("double_blink", [g[0] for g in step.gestures])
        self.assertIn("单击", step.bubble)


class TestMouthReturn(unittest.TestCase):
    def _enter_douyin(self, sm):
        return sm.update(["nod"], "", 0.0)

    def test_single_mouth_open_does_not_return(self):
        sm = make_sm()
        self._enter_douyin(sm)
        step = sm.update(["mouth_open"], "", 1.0)
        self.assertFalse(step.is_menu)
        self.assertIn("再张嘴一次返回", step.bubble)

    def test_two_mouth_opens_return_to_menu(self):
        sm = make_sm()
        self._enter_douyin(sm)
        sm.update(["mouth_open"], "", 1.0)
        step = sm.update(["mouth_open"], "", 2.0)
        self.assertTrue(step.is_menu)
        self.assertIn("返回选择", step.bubble)


class TestHints(unittest.TestCase):
    def test_menu_hint_and_mode_hint(self):
        sm = make_sm()
        menu = sm.update([], "", 0)
        self.assertIn("点头确认", menu.hint)
        sm.update(["nod"], "", 1)
        mode = sm.update([], "", 2)
        self.assertEqual(mode.hint, t(MODE_HINTS[mode.mode]))


if __name__ == "__main__":
    unittest.main()