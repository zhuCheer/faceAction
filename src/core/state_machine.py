"""行为锚定(模态)状态机。

选择态 (mode = None): 右摇下一项 / 左摇上一项 / 点头确认或切换。
- 高亮「看抖音」点头进入看抖音模式（进入即打开抖音）。
- 高亮「防偷窥」点头切换防偷窥开/关，不进入模式。
行为态 (mode == "douyin"): 点头/抬头映射方向键; 双眨眼单击; 连续张嘴两次返回选择态。
"""
from dataclasses import dataclass, field

from i18n import t

from .anti_peep import AntiPeep
from .constants import (
    BEHAVIORS, MODE_ACTIONS, MODE_HINTS, BUBBLE_HOLD_SECONDS,
    MOUTH_RETURN_COUNT, MOUTH_RETURN_WINDOW,
)

_MOVE_LABEL_KEYS = {
    "move_left": "move.move_left", "move_right": "move.move_right",
    "move_up": "move.move_up", "move_down": "move.move_down",
}


@dataclass
class Step:
    mode: str = None                 # None 表示选择态
    menu_index: int = 0
    gestures: list = field(default_factory=list)  # [(name, payload), ...] 待分发
    hint: str = ""
    bubble: str = ""
    continuous: str = ""             # 持续状态文本 ("光标→")
    anti_peep: bool = False          # 防偷窥是否开启
    hidden: bool = False             # 防偷窥: 当前是否处于最小化(隐藏)状态
    stats: dict = field(default_factory=dict)  # 各动作识别次数 (操作统计)
    fps: float = 0.0                 # 由引擎填充
    latency_ms: float = 0.0          # 由引擎填充
    pitch: float = 0.0               # 由引擎填充
    yaw: float = 0.0                 # 由引擎填充
    roll: float = 0.0                # 由引擎填充
    face_present: bool = True        # 由引擎填充

    @property
    def is_menu(self) -> bool:
        return self.mode is None


class BehaviorStateMachine:
    def __init__(self, anti_peep: AntiPeep = None):
        self.anti_peep = anti_peep or AntiPeep()
        self.mode = None
        self.menu_index = 0
        self.action_count = {}
        self._bubble_text = ""
        self._bubble_expire = 0.0
        self._mouth_return_count = 0
        self._last_mouth_return_time = 0.0

    # ------------------------------------------------------------------
    def update(self, events, head_dir, now) -> Step:
        for e in events:
            self.action_count[e] = self.action_count.get(e, 0) + 1

        gestures = []
        fresh_bubble = None

        if self.mode is None:
            fresh_bubble = self._step_menu(events, gestures)
        else:
            fresh_bubble = self._step_mode(events, gestures, now)

        # 气泡保持 (离散优先, 超过保持期后清除)
        if fresh_bubble is not None:
            self._bubble_text = fresh_bubble
            self._bubble_expire = now + BUBBLE_HOLD_SECONDS
        elif self._bubble_text and now > self._bubble_expire:
            self._bubble_text = ""
            self._bubble_expire = 0.0

        return Step(
            mode=self.mode,
            menu_index=self.menu_index,
            gestures=gestures,
            hint=self._hint(),
            bubble=self._bubble_text,
            continuous=self._continuous(head_dir),
            anti_peep=self.anti_peep.enabled,
            hidden=self.anti_peep.hidden,
            stats=dict(self.action_count),
        )

    def return_to_menu(self):
        """从行为态返回选择态 (供 UI 返回按钮调用)。"""
        self.mode = None
        self._mouth_return_count = 0
        self._last_mouth_return_time = 0.0

    # ------------------------------------------------------------------
    def _step_menu(self, events, gestures):
        bubble = None
        for e in events:
            if e in ("shake_right", "shake_left"):
                step = 1 if e == "shake_right" else -1
                self.menu_index = (self.menu_index + step) % len(BEHAVIORS)
                bubble = t("bubble.switch", name=t(BEHAVIORS[self.menu_index][1]))
            elif e == "nod":
                mid = BEHAVIORS[self.menu_index][0]
                if mid == "anti_peep":
                    self.anti_peep.toggle()
                    bubble = t("bubble.anti_peep_on" if self.anti_peep.enabled
                               else "bubble.anti_peep_off")
                else:
                    self.mode = mid
                    self._mouth_return_count = 0
                    self._last_mouth_return_time = 0.0
                    bubble = t("bubble.enter", name=t(BEHAVIORS[self.menu_index][1]))
                    if self.mode == "douyin":
                        gestures.append(("open_douyin", None))
                continue
        return bubble

    def _step_mode(self, events, gestures, now):
        m = self.mode
        bubble = None
        for e in events:
            # 张嘴 = 全局返回手势; 需连续两次张嘴才返回 (降低误触)
            if e == "mouth_open":
                if now - self._last_mouth_return_time > MOUTH_RETURN_WINDOW:
                    self._mouth_return_count = 0
                self._mouth_return_count += 1
                self._last_mouth_return_time = now
                if self._mouth_return_count >= MOUTH_RETURN_COUNT:
                    self.mode = None
                    self._mouth_return_count = 0
                    bubble = t("bubble.return")
                else:
                    bubble = t("bubble.return_again")
                continue

            key = MODE_ACTIONS.get(m, {}).get(e)
            if key:
                gestures.append((e, None))
                bubble = t(key)
        return bubble

    # ------------------------------------------------------------------
    def _hint(self):
        if self.mode is None:
            status = t("state.on" if self.anti_peep.enabled else "state.off")
            return t("hint.menu", status=status)
        return t(MODE_HINTS.get(self.mode, ""))

    def _continuous(self, head_dir):
        if self.mode == "douyin" and head_dir:
            key = _MOVE_LABEL_KEYS.get(head_dir)
            return t(key) if key else ""
        return ""