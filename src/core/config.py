"""配置加载：从 JSON 读取书签、首页、灵敏度等（Python 3.9 兼容，无 TOML 依赖）。"""
import json
import os
import sys
from dataclasses import dataclass, field


@dataclass
class Config:
    homepage: str = "https://www.baidu.com"
    bookmarks: list = field(default_factory=lambda: [
        "https://www.baidu.com",
        "https://www.bilibili.com",
        "https://www.zhihu.com",
        "https://github.com",
    ])
    mouse_step: int = 12          # 鼠标每帧最大移动像素 (比例移动的软上限)
    camera_index: int = 0
    theme: str = "dark"           # 主题：深色 dark / 亮色 light
    language: str = "auto"        # 语言：auto 跟随系统 / zh 中文 / en 英文

    @staticmethod
    def _read_path():
        if getattr(sys, "frozen", False):
            # 打包为 exe 后：优先读取 exe 同级 config/settings.json（用户可改），
            # 不存在则回退到打包内置的 settings.json。
            exe_dir = os.path.dirname(sys.executable)
            user_cfg = os.path.join(exe_dir, "config", "settings.json")
            if os.path.exists(user_cfg):
                return user_cfg
            return os.path.join(
                getattr(sys, "_MEIPASS", exe_dir), "config", "settings.json")
        return os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "config", "settings.json",
        )

    @staticmethod
    def _write_path():
        if getattr(sys, "frozen", False):
            # 写入 exe 同级 config/settings.json（可持久保存用户设置）
            return os.path.join(
                os.path.dirname(sys.executable), "config", "settings.json")
        return Config._read_path()

    @classmethod
    def load(cls, path=None):
        path = path or cls._read_path()
        cfg = cls()
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for k in ("homepage", "mouse_step", "camera_index", "theme", "language"):
                    if k in data:
                        setattr(cfg, k, data[k])
                if data.get("bookmarks"):
                    cfg.bookmarks = [str(b) for b in data["bookmarks"]]
            except (OSError, ValueError):
                pass
        return cfg

    def save(self, path=None):
        path = path or self._write_path()
        data = {}
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except (OSError, ValueError):
                data = {}
        data.update({
            "homepage": self.homepage,
            "bookmarks": list(self.bookmarks),
            "mouse_step": self.mouse_step,
            "camera_index": self.camera_index,
            "theme": self.theme,
            "language": self.language,
        })
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)