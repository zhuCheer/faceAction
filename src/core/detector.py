"""动作检测器：将逐帧 Features 转为离散动作事件列表。

内部维护时序状态（眨眼窗口、冷却、位姿缓冲、静止基线等），
输出事件名与 demo 一致 + 方向化的摇头 (shake_left / shake_right)。
"""
from collections import deque

from .constants import (
    EAR_BLINK_THRESHOLD,
    BLINK_MIN_FRAMES,
    DOUBLE_BLINK_WINDOW_FRAMES,
    LONG_BLINK_FRAMES,
    WINK_MIN_FRAMES,
    WINK_COOLDOWN_FRAMES,
    MAR_OPEN_THRESHOLD,
    MOUTH_HOLD_FRAMES,
    MAR_COOLDOWN_FRAMES,
    TILT_ROLL_THRESHOLD,
    TILT_COOLDOWN_FRAMES,
    PITCH_NOD_THRESHOLD,
    SHAKE_YAW_THRESHOLD,
    NOD_SHAKE_WINDOW,
    NOD_SHAKE_COOLDOWN_FRAMES,
    HEAD_MOVE_YAW_DEADZONE,
    HEAD_MOVE_PITCH_DEADZONE,
    HEAD_MOVE_SMOOTH,
)
from .features import head_move_direction


def _deadzone(value, dz):
    """死区过滤: |value| < dz 归零, 否则去除死区余量 (保留连续量供比例映射)。"""
    if value > dz:
        return value - dz
    if value < -dz:
        return value + dz
    return 0.0


class Detector:
    def __init__(self):
        self.reset()

    def reset(self):
        self.eye_closed_frames = 0
        self.eye_open_frames = 0
        self.left_closed_frames = 0
        self.right_closed_frames = 0
        self.wink_cooldown = 0
        self.mouth_open_frames = 0
        self.mouth_closed_frames = 0
        self.mouth_state = "closed"
        self.mouth_cooldown = 0
        self.pose_buffer = deque(maxlen=NOD_SHAKE_WINDOW)
        self.nod_shake_cooldown = 0
        self.frame_index = 0
        self.pending_blink_frame = None
        self.tilt_cooldown = 0
        self.tilt_armed = True
        self.head_dir = ""
        self.baseline_pitch = 0.0
        self.baseline_yaw = 0.0
        self.baseline_roll = 0.0
        self.head_norm_x = 0.0
        self.head_norm_y = 0.0

    @property
    def is_mouth_open(self) -> bool:
        return self.mouth_state == "open"

    # ------------------------------------------------------------------
    def feed(self, f) -> list:
        events = []

        # 眨眼 (单击 / 双眨眼 / 长眨眼)
        self.frame_index += 1
        if f.ear < EAR_BLINK_THRESHOLD:
            self.eye_closed_frames += 1
            self.eye_open_frames = 0
        else:
            if self.eye_open_frames == 0 and self.eye_closed_frames >= BLINK_MIN_FRAMES:
                self._on_blink_cycle(self.eye_closed_frames, events)
            self.eye_closed_frames = 0
            self.eye_open_frames += 1
        if (self.pending_blink_frame is not None
                and self.frame_index - self.pending_blink_frame > DOUBLE_BLINK_WINDOW_FRAMES):
            events.append("blink")
            self.pending_blink_frame = None

        # 单眼闭合 (wink)
        if self.wink_cooldown > 0:
            self.wink_cooldown -= 1
        left_closed = f.ear_left < EAR_BLINK_THRESHOLD and f.ear_left < f.ear_right * 0.55
        right_closed = f.ear_right < EAR_BLINK_THRESHOLD and f.ear_right < f.ear_left * 0.55
        if left_closed:
            self.left_closed_frames += 1
        else:
            if self.left_closed_frames >= WINK_MIN_FRAMES and self.wink_cooldown == 0:
                events.append("wink_left")
                self.wink_cooldown = WINK_COOLDOWN_FRAMES
            self.left_closed_frames = 0
        if right_closed:
            self.right_closed_frames += 1
        else:
            if self.right_closed_frames >= WINK_MIN_FRAMES and self.wink_cooldown == 0:
                events.append("wink_right")
                self.wink_cooldown = WINK_COOLDOWN_FRAMES
            self.right_closed_frames = 0

        # 歪头: 以平滑基线为参照，仅真实侧倾才判定 (避免静止/头部转动误触)
        self.baseline_roll += HEAD_MOVE_SMOOTH * (f.roll - self.baseline_roll)
        tilt = self._detect_tilt(f.roll - self.baseline_roll)
        if tilt:
            events.append(tilt)
            self.pose_buffer.clear()
            self.nod_shake_cooldown = 0
            self.head_dir = ""

        # 头部连续方向 (始终计算, 供鼠标/方向键模式使用)
        self.baseline_pitch += HEAD_MOVE_SMOOTH * (f.pitch - self.baseline_pitch)
        self.baseline_yaw += HEAD_MOVE_SMOOTH * (f.yaw - self.baseline_yaw)
        dpitch = f.pitch - self.baseline_pitch
        dyaw = f.yaw - self.baseline_yaw
        self.head_dir = head_move_direction(
            dpitch, -dyaw, HEAD_MOVE_YAW_DEADZONE, HEAD_MOVE_PITCH_DEADZONE)
        # 死区后的连续偏移 (供鼠标比例移动使用; 右/下为正)
        self.head_norm_x = _deadzone(-dyaw, HEAD_MOVE_YAW_DEADZONE)
        self.head_norm_y = _deadzone(dpitch, HEAD_MOVE_PITCH_DEADZONE)

        # 张嘴 (状态机 closed <-> open)
        if self.mouth_cooldown > 0:
            self.mouth_cooldown -= 1
        if f.mar > MAR_OPEN_THRESHOLD:
            self.mouth_open_frames += 1
            self.mouth_closed_frames = 0
            if self.mouth_state == "closed" and self.mouth_open_frames >= MOUTH_HOLD_FRAMES \
                    and self.mouth_cooldown == 0:
                self.mouth_state = "open"
                events.append("mouth_open")
                self.mouth_cooldown = MAR_COOLDOWN_FRAMES
        else:
            self.mouth_open_frames = 0
            self.mouth_closed_frames += 1
            if self.mouth_state == "open" and self.mouth_closed_frames >= MOUTH_HOLD_FRAMES \
                    and self.mouth_cooldown == 0:
                self.mouth_state = "closed"
                events.append("mouth_close")
                self.mouth_cooldown = MAR_COOLDOWN_FRAMES

        # 点头 / 方向化摇头
        if self.nod_shake_cooldown > 0:
            self.nod_shake_cooldown -= 1
        self.pose_buffer.append((f.pitch, f.yaw))
        if self.nod_shake_cooldown == 0 and len(self.pose_buffer) >= 8:
            action = self._detect_nod_shake()
            if action:
                events.append(action)
                self.nod_shake_cooldown = NOD_SHAKE_COOLDOWN_FRAMES

        return events

    # ------------------------------------------------------------------
    def _on_blink_cycle(self, duration, events):
        if duration >= LONG_BLINK_FRAMES:
            events.append("long_blink")
            self.pending_blink_frame = None
            return
        if (self.pending_blink_frame is not None
                and self.frame_index - self.pending_blink_frame <= DOUBLE_BLINK_WINDOW_FRAMES):
            events.append("double_blink")
            self.pending_blink_frame = None
            return
        self.pending_blink_frame = self.frame_index

    def _detect_tilt(self, roll):
        if self.tilt_cooldown > 0:
            self.tilt_cooldown -= 1
            return None
        if abs(roll) < TILT_ROLL_THRESHOLD * 0.5:
            self.tilt_armed = True
        if not self.tilt_armed:
            return None
        if roll > TILT_ROLL_THRESHOLD:
            self.tilt_armed = False
            self.tilt_cooldown = TILT_COOLDOWN_FRAMES
            return "tilt_right"
        if roll < -TILT_ROLL_THRESHOLD:
            self.tilt_armed = False
            self.tilt_cooldown = TILT_COOLDOWN_FRAMES
            return "tilt_left"
        return None

    def _detect_nod_shake(self):
        pitches = [p for p, _ in self.pose_buffer]
        yaws = [y for _, y in self.pose_buffer]
        p_range = max(pitches) - min(pitches)
        y_range = max(yaws) - min(yaws)
        p_net = abs(pitches[-1] - pitches[0])
        y_net = abs(yaws[-1] - yaws[0])
        if p_range > PITCH_NOD_THRESHOLD and p_range > y_range * 1.2 \
                and p_net < p_range * 0.5:
            # 以窗口首帧为基准区分方向: 低头(正峰) -> nod; 抬头(负谷) -> nod_up
            up_amp = max(pitches) - pitches[0]
            down_amp = pitches[0] - min(pitches)
            return "nod" if up_amp >= down_amp else "nod_up"
        if y_range > SHAKE_YAW_THRESHOLD and y_range > p_range * 1.2 \
                and y_net < y_range * 0.5:
            extreme = max(yaws, key=abs)
            return "shake_right" if extreme < 0 else "shake_left"
        return None