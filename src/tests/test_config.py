"""config 层单元测试：默认值与 JSON 加载。"""
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import Config


class TestConfig(unittest.TestCase):
    def test_defaults(self):
        cfg = Config()
        self.assertEqual(cfg.homepage, "https://www.baidu.com")
        self.assertGreater(len(cfg.bookmarks), 0)

    def test_load_overrides(self):
        fd, path = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump({
                    "homepage": "https://example.com",
                    "bookmarks": ["https://a.com", "https://b.com"],
                    "mouse_step": 24,
                    "camera_index": 2,
                }, f)
            cfg = Config.load(path)
            self.assertEqual(cfg.homepage, "https://example.com")
            self.assertEqual(cfg.bookmarks, ["https://a.com", "https://b.com"])
            self.assertEqual(cfg.mouse_step, 24)
            self.assertEqual(cfg.camera_index, 2)
        finally:
            os.remove(path)

    def test_load_missing_file_uses_defaults(self):
        cfg = Config.load(os.path.join(tempfile.gettempdir(), "no_such_file.json"))
        self.assertEqual(cfg.homepage, "https://www.baidu.com")


if __name__ == "__main__":
    unittest.main()