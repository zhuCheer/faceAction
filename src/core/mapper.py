"""指令映射：把 (模式, 动作) 解析为可执行的 Command。

仅看抖音模式：进入即打开抖音网址; 点头/抬头映射为上/下方向键, 快速眨眼单击。
"""
from dataclasses import dataclass

from .constants import DOUYIN_URL


@dataclass
class Command:
    kind: str = ""        # "mouse" | "key" | "browser"
    action: str = ""      # click / double_click / drag_toggle / tap / open ...
    key: str = ""         # 键名 (由 executor 映射为 vk)
    url: str = ""


class Mapper:
    def __init__(self, homepage: str = ""):
        self.homepage = homepage or "https://www.baidu.com"

    def map(self, mode, gesture, payload) -> Command or None:
        if mode == "douyin":
            if gesture == "open_douyin":
                return Command("browser", "open", url=DOUYIN_URL)
            return {
                "nod": Command("key", "tap", "DOWN"),
                "nod_up": Command("key", "tap", "UP"),
                "double_blink": Command("mouse", "click"),
            }.get(gesture)
        return None