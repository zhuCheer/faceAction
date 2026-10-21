"""识别引擎：串起 跟踪 → 特征 → 检测 → 状态机 → 映射 → 执行。

对外暴露 process_frame(bgr) -> (step, display_bgr, landmarks)，
并维护遥测 (FPS/延迟/位姿) 与运行日志 (通过 take_logs 拉取)。
"""
import math
import time

import cv2

from i18n import t

from .config import Config
from .constants import MOUSE_SMOOTH, MOUSE_GAIN, DOUYIN_URL
from .detector import Detector
from .executor import Executor
from .mapper import Mapper
from .state_machine import BehaviorStateMachine, Step
from .tracker import FaceTracker


class RecognitionEngine:
    def __init__(self, config: Config, executor: Executor = None):
        self.config = config
        self.tracker = FaceTracker()
        self.detector = Detector()
        self.sm = BehaviorStateMachine()
        self.mapper = Mapper(config.homepage)
        self.executor = executor or Executor()
        self._last_mode = None
        self._last_anti_peep = None
        self._mouse_vx = 0.0
        self._mouse_vy = 0.0

        # 遥测
        self._fps = 0.0
        self._last_ts = None
        self._boot_logged = False

        # 运行日志缓冲 (由 process_frame 填充, 供 UI 每次帧后拉取)
        self._pending_logs = []
        self.log(t("log.boot"))

    # ------------------------------------------------------------------
    def log(self, message: str, level: str = "info") -> None:
        """追加一条运行日志。level: info / ok / warn。"""
        self._pending_logs.append((time.strftime("%H:%M:%S"), message, level))

    def take_logs(self) -> list:
        """取出并清空尚未被消费的日志。"""
        logs = self._pending_logs
        self._pending_logs = []
        return logs

    # ------------------------------------------------------------------
    def process_frame(self, bgr):
        t0 = time.time()
        now = t0

        # FPS (指数滑动平均)
        if self._last_ts is not None:
            dt = now - self._last_ts
            if dt > 1e-3:
                inst = 1.0 / dt
                self._fps = inst if self._fps <= 0 else self._fps * 0.9 + inst * 0.1
        self._last_ts = now

        frame_shape = bgr.shape
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        results = self.tracker.detect(rgb)
        if not self._boot_logged:
            self._boot_logged = True
            self.log(t("log.facemesh_ready"))
        faces = self.tracker.all_landmarks(results, frame_shape)
        landmarks = faces[0] if faces else None

        # 防偷窥: 仅「恰好 1 张脸」视为安全; 0 张(离开) 或 多张(有人偷看) 都触发隐藏
        self._handle_anti_peep(len(faces) == 1, now)

        if landmarks is None:
            self.detector.reset()
            self._release_continuous()
            # 保留当前模式 (看抖音态跨越无人脸), 仅提示无人脸
            step = Step(
                mode=self.sm.mode,
                menu_index=self.sm.menu_index,
                hint=t("noface.tip"),
                anti_peep=self.sm.anti_peep.enabled,
                hidden=self.sm.anti_peep.hidden,
                stats=dict(self.sm.action_count),
            )
            self._finalize_step(step, t0, pitch=0.0, yaw=0.0, roll=0.0, face_present=False)
            return step, bgr, None

        feats = self.tracker.features(landmarks, frame_shape)
        events = self.detector.feed(feats)
        step = self.sm.update(events, self.detector.head_dir, now)

        # 1) 分发离散指令
        for gesture, payload in step.gestures:
            cmd = self.mapper.map(step.mode, gesture, payload)
            self.executor.execute(cmd)

        # 2) 持续指令 (鼠标移动 / 方向键)
        self._handle_continuous(step.mode, self.detector.head_dir)

        # 模式切换时释放持续占用，并记录日志
        if step.mode != self._last_mode:
            self._release_continuous()
            if step.mode == "douyin":
                self.log(t("log.enter_douyin"))
            elif self._last_mode == "douyin":
                self.log(t("log.return_menu"))
            self._last_mode = step.mode

        # 防偷窥开关变化
        if self._last_anti_peep is not None and step.anti_peep != self._last_anti_peep:
            if step.anti_peep:
                self.log(t("log.anti_peep_on"), "ok")
            else:
                self.log(t("log.anti_peep_off"), "warn")
        self._last_anti_peep = step.anti_peep

        # 选择态(大窗)叠加主脸轮廓网格; 所有场景都给每张人脸画外接框便于确认多脸
        if step.is_menu:
            display = self.tracker.draw_mesh(bgr, landmarks)
        else:
            display = bgr
        display = self.tracker.draw_face_boxes(display, faces)

        self._finalize_step(step, t0, feats.pitch, feats.yaw, feats.roll, face_present=True)
        return step, display, landmarks

    # ------------------------------------------------------------------
    def _finalize_step(self, step, t0, pitch, yaw, roll, face_present):
        step.fps = round(self._fps, 1)
        step.latency_ms = round((time.time() - t0) * 1000.0, 1)
        step.pitch = round(float(pitch), 1)
        step.yaw = round(float(yaw), 1)
        step.roll = round(float(roll), 1)
        step.face_present = face_present

    def _handle_anti_peep(self, safe, now):
        """safe = 恰好 1 张脸; 0 张或多张都视为不安全, 由 AntiPeep 做非对称防抖。"""
        watching = (self.sm.mode == "douyin")
        for cmd in self.sm.anti_peep.on_face(safe, watching, now):
            if cmd == "hide":
                self.executor.show_desktop()
                self.log(t("log.no_face_hide"), "warn")
            elif cmd == "restore":
                self.executor.restore_douyin(DOUYIN_URL)
                self.log(t("log.face_restore"), "ok")

    def _handle_continuous(self, mode, head_dir):
        if mode == "douyin":
            # 头部连续偏移 -> 低通平滑 -> 软饱和比例移动 (轻移慢、重移快且有上限)
            nx = self.detector.head_norm_x
            ny = self.detector.head_norm_y
            self._mouse_vx += MOUSE_SMOOTH * (nx - self._mouse_vx)
            self._mouse_vy += MOUSE_SMOOTH * (ny - self._mouse_vy)
            step = self.config.mouse_step
            dx = int(round(step * math.tanh(self._mouse_vx * MOUSE_GAIN)))
            dy = int(round(step * math.tanh(self._mouse_vy * MOUSE_GAIN)))
            if dx or dy:
                self.executor.mouse_move_rel(dx, dy)

    def _release_continuous(self):
        self.executor.release_direction()

    def close(self):
        self._release_continuous()
        self.executor.release_all()
        self.tracker.close()