"""mapper 层单元测试：看抖音动作 -> 指令映射。"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.mapper import Mapper, Command


class TestMapper(unittest.TestCase):
    def setUp(self):
        self.m = Mapper("https://www.baidu.com")

    def test_douyin(self):
        self.assertEqual(
            self.m.map("douyin", "open_douyin", None),
            Command("browser", "open", url="https://www.douyin.com/"))
        self.assertEqual(self.m.map("douyin", "nod", None).key, "DOWN")
        self.assertEqual(self.m.map("douyin", "nod_up", None).key, "UP")
        self.assertEqual(self.m.map("douyin", "double_blink", None), Command("mouse", "click"))
        self.assertIsNone(self.m.map("douyin", "blink", None))

    def test_unknown_mode_returns_none(self):
        self.assertIsNone(self.m.map("mouse", "blink", None))
        self.assertIsNone(self.m.map(None, "nod", None))


if __name__ == "__main__":
    unittest.main()