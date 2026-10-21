"""防偷窥控制器：根据人脸出现/消失输出 hide / restore 命令。

纯逻辑模块，不依赖 UI 与系统调用，便于单元测试。

防抖策略（非对称）：
- 最小化 (hide)：人脸离开时，若正在刷抖音 (watching=True)，立即触发，无延时
  （隐私优先，尽快最小化）；已是最小化状态则不会重复触发。
- 恢复 (restore)：人脸回归后需连续 stable_confirm_seconds 无波动才触发。
  期间任何检测波动（人脸消失再出现）都会重置计时，避免页面闪烁。
"""
from .constants import ANTI_PEEP_RESTORE_DEBOUNCE_SECONDS


class AntiPeep:
    def __init__(self, restore_debounce_seconds: float = ANTI_PEEP_RESTORE_DEBOUNCE_SECONDS):
        self.enabled = False
        self.restore_debounce_seconds = restore_debounce_seconds
        self.face_present = True      # 最近一帧是否检测到人脸 (已确认的稳定状态)
        self.hidden = False           # 是否已触发最小化 (Win+D 显示桌面)
        self._stable_since = 0.0      # 人脸稳定存在的起始时刻 (用于恢复防抖)

    def toggle(self) -> None:
        """切换开/关。"""
        self.enabled = not self.enabled
        if not self.enabled:
            self._reset()

    def _reset(self) -> None:
        self._stable_since = 0.0

    def on_face(self, present: bool, watching: bool, now: float) -> list:
        """根据人脸状态与是否在刷抖音返回待执行命令：["hide"] / ["restore"] / []。

        - present: 是否检测到人脸。
        - watching: 是否正在刷抖音（看抖音模式）；仅该状态人脸离开才会触发最小化。
        - now: 当前时间戳 (秒)。
        """
        if not self.enabled:
            # 关闭时仅同步状态、不输出命令，并复位为未隐藏。
            self.face_present = present
            self.hidden = False
            self._reset()
            return []

        if present == self.face_present:
            # 状态未变化：仅在「已隐藏且人脸在场」时继续累计稳定确认。
            if self.hidden and present:
                if self._stable_since > 0 and now - self._stable_since >= self.restore_debounce_seconds:
                    # 持续稳定足够时长，触发恢复
                    self.hidden = False
                    self._stable_since = 0.0
                    return ["restore"]
            return []

        # 状态发生变化
        if present:
            # 人脸回归：开始稳定确认计时（仅当处于隐藏状态时才可能触发恢复）。
            self.face_present = True
            if self.hidden:
                self._stable_since = now  # 开始稳定确认计时
            return []

        # 人脸离开：正在刷抖音且尚未最小化时才立即最小化。
        # 同时重置稳定计时，避免之前的回归计时导致误触发
        self.face_present = False
        self._stable_since = 0.0  # 波动：重置稳定计时
        if watching and not self.hidden:
            self.hidden = True
            return ["hide"]
        return []