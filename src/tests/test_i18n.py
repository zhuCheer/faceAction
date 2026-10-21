"""i18n 层单元测试：中英切换、系统跟随、英语兜底。"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import i18n


def tearDownModule():
    i18n.set_language("auto")


class TestLanguageResolution(unittest.TestCase):
    def test_supported_languages(self):
        self.assertEqual(set(i18n.SUPPORTED_LANGUAGES), {"zh", "en"})

    def test_explicit_language(self):
        i18n.set_language("zh")
        self.assertEqual(i18n.effective_language(), "zh")
        i18n.set_language("en")
        self.assertEqual(i18n.effective_language(), "en")

    def test_unknown_falls_back_to_english(self):
        i18n.set_language("fr")
        self.assertEqual(i18n.effective_language(), "en")

    def test_auto_is_supported(self):
        i18n.set_language("auto")
        self.assertIn(i18n.effective_language(), i18n.SUPPORTED_LANGUAGES)


class TestTranslate(unittest.TestCase):
    def test_zh_en_switch(self):
        i18n.set_language("zh")
        self.assertEqual(i18n.t("behavior.douyin"), "看抖音")
        i18n.set_language("en")
        self.assertEqual(i18n.t("behavior.douyin"), "Watch Douyin")

    def test_format_kwargs(self):
        i18n.set_language("zh")
        self.assertEqual(i18n.t("stat.count", n=3), "3次")
        i18n.set_language("en")
        self.assertEqual(i18n.t("stat.count", n=3), "3")

    def test_unknown_key_falls_back(self):
        i18n.set_language("zh")
        self.assertEqual(i18n.t("no.such.key"), "no.such.key")


if __name__ == "__main__":
    unittest.main()