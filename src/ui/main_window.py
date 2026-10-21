"""主窗口：玻璃拟态深色界面。

- 选择态 (menu)：完整控制面板 —— 左侧实时预览 + 两张模式卡 + 右侧
  「动作识别 / 运行日志 / 系统状态」数据面板。
- 行为态 (active)：小窗悬浮于右下角，仅保留视频预览与识别提示。
"""
import html
import time
from collections import deque

import cv2
from PySide6.QtCore import Qt, QThread, Signal, QRectF
from PySide6.QtGui import QColor, QImage, QPainter, QPen, QPainterPath, QGuiApplication
from PySide6.QtWidgets import (
    QApplication, QFrame, QGridLayout, QHBoxLayout, QLabel, QLayout,
    QProgressBar, QPushButton, QTextEdit, QVBoxLayout, QWidget,
)

import i18n
from core.constants import BEHAVIORS
from ui import theme as T

MENU_SIZE = (1160, 740)
ACTIVE_SIZE = (220, 280)

# 动作识别面板展示的 5 类手势 (事件名, 显示名 i18n key)
GESTURE_ROWS = [
    ("nod", "gesture.nod"),
    ("nod_up", "gesture.nod_up"),
    ("shake_left", "gesture.shake_left"),
    ("shake_right", "gesture.shake_right"),
    ("mouth_open", "gesture.mouth_open"),
]


def _log_colors():
    t = T.get_tokens()
    return {
        "info": t["TEXT_SECONDARY"],
        "ok": t["GREEN"],
        "warn": t["RED"],
    }


def mode_name(mode):
    for mid, key in BEHAVIORS:
        if mid == mode:
            return i18n.t(key)
    return ""


def bgr_to_qimage(bgr):
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    h, w, ch = rgb.shape
    return QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888).copy()


class CameraThread(QThread):
    frame_ready = Signal(object)

    def __init__(self, engine, camera_index=0, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.camera_index = camera_index
        self._running = False

    def run(self):
        cap = cv2.VideoCapture(self.camera_index)
        if not cap.isOpened():
            self.engine.log(i18n.t("log.camera_error", index=self.camera_index), "warn")
            self.frame_ready.emit({
                "error": i18n.t("log.camera_error", index=self.camera_index),
                "logs": self.engine.take_logs(),
            })
            return
        self.engine.log(i18n.t("log.camera_ready"), "ok")
        self._running = True
        while self._running:
            ok, frame = cap.read()
            if not ok:
                time.sleep(0.01)
                continue
            step, display, _ = self.engine.process_frame(frame)
            disp = cv2.flip(display, 1)
            self.frame_ready.emit({
                "image": bgr_to_qimage(disp),
                "step": step,
                "logs": self.engine.take_logs(),
            })
        cap.release()

    def stop(self):
        self._running = False
        self.wait(2000)


class FrameView(QWidget):
    """视频预览：深色底 + 圆角裁切绘制摄像头画面。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._img = None
        self._drag = None
        self.setMinimumSize(40, 30)

    def set_image(self, img):
        self._img = img
        self.update()

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._drag = e.globalPosition().toPoint() - self.window().frameGeometry().topLeft()

    def mouseMoveEvent(self, e):
        if self._drag is not None and e.buttons() & Qt.LeftButton:
            self.window().move(e.globalPosition().toPoint() - self._drag)

    def mouseReleaseEvent(self, _):
        self._drag = None

    def paintEvent(self, _):
        t = T.get_tokens()
        border = QColor(t["ACCENT"])
        border.setAlpha(60)
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        radius = 14
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), radius, radius)
        p.setClipPath(path)
        p.fillRect(self.rect(), QColor(t["VIDEO_BG"]))
        if self._img is not None:
            scaled = self._img.scaled(
                self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            x = (self.width() - scaled.width()) // 2
            y = (self.height() - scaled.height()) // 2
            p.drawImage(x, y, scaled)
        p.setClipping(False)
        p.setPen(QPen(border, 1))
        p.drawPath(path)
        p.end()


class ToggleSwitch(QWidget):
    """防偷窥开关：圆角轨道 + 可滑动圆点。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Toggle")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setFixedSize(52, 28)
        self._on = False
        self._knob = QLabel(self)
        self._knob.setObjectName("ToggleKnob")
        self._knob.setFixedSize(20, 20)
        self.set_on(False)

    def set_on(self, on):
        self._on = bool(on)
        self.setProperty("on", self._on)
        self.style().unpolish(self)
        self.style().polish(self)
        self._knob.move(27 if self._on else 3, 4)


class TitleBar(QWidget):
    """标题栏：支持拖拽移动窗口。"""

    def __init__(self, window, parent=None):
        super().__init__(parent)
        self._window = window
        self._drag = None

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._drag = e.globalPosition().toPoint() - self._window.frameGeometry().topLeft()

    def mouseMoveEvent(self, e):
        if self._drag is not None and e.buttons() & Qt.LeftButton:
            self._window.move(e.globalPosition().toPoint() - self._drag)

    def mouseReleaseEvent(self, _):
        self._drag = None


class MainWindow(QWidget):
    def __init__(self, config, engine):
        super().__init__()
        self.config = config
        self.engine = engine
        self._last_is_menu = None
        self._logs = deque(maxlen=24)

        # 供 _retranslate 遍历的可翻译控件
        self._metric_small = []
        self._panel_titles = []
        self._gesture_row_names = []
        self._sys_rows = []
        self._hint_items = []

        self.setObjectName("Root")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        self._build_ui()

        self.thread = CameraThread(engine, config.camera_index, self)
        self.thread.frame_ready.connect(self.on_frame)
        self.thread.start()

    # ------------------------------------------------------------------
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSizeConstraint(QLayout.SetNoConstraint)

        self.glass = QWidget()
        self.glass.setObjectName("GlassWindow")
        self.glass.setAttribute(Qt.WA_StyledBackground, True)
        root.addWidget(self.glass)

        glass = QVBoxLayout(self.glass)
        glass.setContentsMargins(14, 12, 14, 14)
        glass.setSpacing(12)

        glass.addWidget(self._build_titlebar())
        glass.addWidget(self._build_body(), 1)
        self.hint_bar = self._build_hintbar()
        glass.addWidget(self.hint_bar)

        self._apply_state(True)

    # ------------------------------------------------------------------
    def _pill(self, dot_color, text):
        lbl = QLabel(
            f'<span style="color:{dot_color}">●</span> {text}')
        lbl.setObjectName("StatusPill")
        lbl.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        return lbl

    def _set_pill(self, pill, dot_color, text):
        pill.setText(f'<span style="color:{dot_color}">●</span> {text}')

    def _build_titlebar(self):
        bar = TitleBar(self)
        bar.setObjectName("TitleBar")
        bar.setAttribute(Qt.WA_StyledBackground, True)
        hd = QHBoxLayout(bar)
        hd.setContentsMargins(14, 0, 0, 0)
        hd.setSpacing(8)

        self.logo = QLabel("FA")
        self.logo.setObjectName("Logo")
        self.logo.setFixedSize(26, 26)
        self.logo.setAlignment(Qt.AlignCenter)
        self.logo.setAttribute(Qt.WA_TransparentForMouseEvents, True)

        self.app_title = QLabel("FaceAction")
        self.app_title.setObjectName("Title")
        self.app_title.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.title_sub = QLabel(i18n.t("title_sub"))
        self.title_sub.setObjectName("TitleSub")
        self.title_sub.setAttribute(Qt.WA_TransparentForMouseEvents, True)

        t = T.get_tokens()
        self.camera_pill = self._pill(t["GREEN"], i18n.t("camera_connected"))
        self.guard_pill = self._pill(t["ACCENT"], i18n.t("guard_on"))
        self.guard_pill.setVisible(False)

        self.theme_btn = QPushButton()
        self.theme_btn.setObjectName("ThemeBtn")
        self.theme_btn.setCursor(Qt.PointingHandCursor)
        self.theme_btn.clicked.connect(self._toggle_theme)

        self.lang_btn = QPushButton()
        self.lang_btn.setObjectName("LangBtn")
        self.lang_btn.setCursor(Qt.PointingHandCursor)
        self.lang_btn.clicked.connect(self._toggle_language)

        hd.addWidget(self.logo)
        hd.addWidget(self.app_title)
        hd.addWidget(self.title_sub)
        hd.addSpacing(12)
        hd.addWidget(self.camera_pill)
        hd.addWidget(self.guard_pill)
        hd.addWidget(self.theme_btn)
        hd.addWidget(self.lang_btn)
        hd.addStretch(1)

        self.return_btn = QPushButton(i18n.t("return_btn"))
        self.return_btn.setObjectName("WinButton")
        self.return_btn.setFixedSize(60, 32)
        self.return_btn.setCursor(Qt.PointingHandCursor)
        self.return_btn.clicked.connect(self._return_to_menu)

        self.min_btn = QPushButton("\u2014")
        self.min_btn.setObjectName("WinButton")
        self.min_btn.setFixedSize(46, 32)
        self.min_btn.setCursor(Qt.PointingHandCursor)
        self.min_btn.clicked.connect(self.showMinimized)

        self.max_btn = QPushButton("\u25a1")
        self.max_btn.setObjectName("WinButton")
        self.max_btn.setFixedSize(46, 32)
        self.max_btn.setCursor(Qt.PointingHandCursor)
        self.max_btn.clicked.connect(self._toggle_maximize)

        close_btn = QPushButton("\u00d7")
        close_btn.setObjectName("WinClose")
        close_btn.setFixedSize(46, 32)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.clicked.connect(self.close)

        hd.addWidget(self.return_btn)
        hd.addWidget(self.min_btn)
        hd.addWidget(self.max_btn)
        hd.addWidget(close_btn)

        self._update_theme_text()
        self._update_lang_text()
        return bar

    def _toggle_theme(self):
        T.set_theme("light" if T.get_theme() == "dark" else "dark")
        self.config.theme = T.get_theme()
        try:
            self.config.save()
        except OSError:
            pass
        self._apply_theme()

    def _apply_theme(self):
        app = QApplication.instance()
        app.setStyleSheet(T.build_stylesheet())
        self._update_theme_text()

        t = T.get_tokens()
        self._set_pill(self.camera_pill, t["GREEN"], i18n.t("camera_connected"))
        self._set_pill(self.guard_pill, t["ACCENT"], i18n.t("guard_on"))
        self._render_logs()
        self.video.update()

    def _update_theme_text(self):
        if T.get_theme() == "light":
            self.theme_btn.setText(i18n.t("theme_light"))
        else:
            self.theme_btn.setText(i18n.t("theme_dark"))

    def _lang_label(self):
        return i18n.LANGUAGE_NAMES.get(i18n.effective_language(), "")

    def _update_lang_text(self):
        self.lang_btn.setText(self._lang_label())

    def _toggle_language(self):
        cur = i18n.effective_language()
        i18n.set_language("en" if cur == "zh" else "zh")
        self.config.language = i18n.get_language()
        try:
            self.config.save()
        except OSError:
            pass
        self._retranslate()

    def _retranslate(self):
        """语言切换后刷新所有静态文案（动态遥测由下一帧刷新）。"""
        self.title_sub.setText(i18n.t("title_sub"))
        self.return_btn.setText(i18n.t("return_btn"))
        self._update_lang_text()

        t = T.get_tokens()
        self._set_pill(self.camera_pill, t["GREEN"], i18n.t("camera_connected"))
        self._set_pill(self.guard_pill, t["ACCENT"], i18n.t("guard_on"))

        for card in self.cards:
            for lbl, key in getattr(card, "_i18n", []):
                lbl.setText(i18n.t(key))

        if self.use_tag is not None:
            self.use_tag.setText(i18n.t("use.tag"))

        for lbl, key in self._metric_small:
            lbl.setText(i18n.t(key))

        self.hud_tl.setText(i18n.t("hud.live"))
        self.no_face.setText(i18n.t("noface.mask"))

        for lbl, key in self._panel_titles:
            lbl.setText(i18n.t(key))
        for lbl, key in self._gesture_row_names:
            lbl.setText(i18n.t(key))
        for kk, k_key, vv, v_key in self._sys_rows:
            kk.setText(i18n.t(k_key))
            if v_key:
                vv.setText(i18n.t(v_key))
        self.privacy_note.setText(i18n.t("privacy.note"))
        for k, k_key, t_lbl, t_key in self._hint_items:
            k.setText(i18n.t(k_key))
            t_lbl.setText(i18n.t(t_key))

    def _toggle_maximize(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def _return_to_menu(self):
        self.engine.sm.return_to_menu()

    # ------------------------------------------------------------------
    def _build_body(self):
        body = QWidget()
        hb = QHBoxLayout(body)
        hb.setContentsMargins(0, 0, 0, 0)
        hb.setSpacing(14)

        hb.addWidget(self._build_main_col(), 1)
        self.side_col = self._build_side_col()
        hb.addWidget(self.side_col, 0)
        return body

    def _build_main_col(self):
        col = QWidget()
        v = QVBoxLayout(col)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(14)

        v.addWidget(self._build_video_frame(), 1)

        self.menu_bar = QWidget()
        mb = QHBoxLayout(self.menu_bar)
        mb.setContentsMargins(0, 0, 0, 0)
        mb.setSpacing(14)
        self.card_douyin, self.use_tag = self._build_card(
            "▶", "behavior.douyin", "card.douyin_sub", "card.douyin_kbd")
        self.card_guard, guard_toggle, guard_label = self._build_card(
            "◈", "behavior.anti_peep", "card.guard_sub", "card.guard_kbd",
            with_toggle=True)
        self.guard_toggle = guard_toggle
        self.guard_toggle_label = guard_label
        self.cards = [self.card_douyin, self.card_guard]
        mb.addWidget(self.card_douyin)
        mb.addWidget(self.card_guard)
        v.addWidget(self.menu_bar)
        return col

    def _build_card(self, icon, title_key, sub_key, kbd_key, with_toggle=False):
        card = QWidget()
        card.setObjectName("MenuCard")
        card.setAttribute(Qt.WA_StyledBackground, True)
        lay = QHBoxLayout(card)
        lay.setContentsMargins(18, 16, 18, 16)
        lay.setSpacing(14)

        ic = QLabel(icon)
        ic.setObjectName("CardIcon")
        ic.setFixedSize(52, 52)
        ic.setAlignment(Qt.AlignCenter)

        text_col = QVBoxLayout()
        text_col.setSpacing(3)
        t = QLabel(i18n.t(title_key))
        t.setObjectName("CardTitle")
        s = QLabel(i18n.t(sub_key))
        s.setObjectName("CardSub")
        s.setWordWrap(True)
        k = QLabel(i18n.t(kbd_key))
        k.setObjectName("CardKbd")
        text_col.addWidget(t)
        text_col.addWidget(s)
        text_col.addWidget(k)

        lay.addWidget(ic)
        lay.addLayout(text_col, 1)

        card._i18n = [(t, title_key), (s, sub_key), (k, kbd_key)]

        if with_toggle:
            tail = QVBoxLayout()
            tail.setSpacing(4)
            label = QLabel(i18n.t("toggle.off"))
            label.setObjectName("ToggleLabel")
            label.setAlignment(Qt.AlignHCenter)
            toggle = ToggleSwitch()
            tail.addWidget(label, 0, Qt.AlignHCenter)
            tail.addWidget(toggle, 0, Qt.AlignHCenter)
            lay.addLayout(tail, 0)
            return card, toggle, label

        use_tag = QLabel(i18n.t("use.tag"))
        use_tag.setObjectName("UseTag")
        use_tag.setVisible(False)
        lay.addWidget(use_tag, 0, Qt.AlignTop)
        return card, use_tag

    # ------------------------------------------------------------------
    def _build_video_frame(self):
        frame = QFrame()
        frame.setObjectName("VideoFrame")
        grid = QGridLayout(frame)
        grid.setContentsMargins(0, 0, 0, 0)

        self.video = FrameView()
        grid.addWidget(self.video, 0, 0)

        overlay = QWidget()
        overlay.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        ov = QGridLayout(overlay)
        ov.setContentsMargins(12, 12, 12, 12)
        ov.setRowStretch(1, 1)

        # 左上: 实时检测
        self.hud_tl = QLabel(i18n.t("hud.live"))
        self.hud_tl.setObjectName("Hud")
        # 右上: FPS / 延迟
        self.hud_tr = QLabel(f"FPS 0.0 | {i18n.t('hud.latency')} 0ms")
        self.hud_tr.setObjectName("HudMono")

        # 右下: 位姿指标 + 状态
        self.hud_bl = QWidget()
        self.hud_bl.setObjectName("HudBox")
        self.hud_bl.setAttribute(Qt.WA_StyledBackground, True)
        hbl = QHBoxLayout(self.hud_bl)
        hbl.setContentsMargins(12, 8, 12, 8)
        hbl.setSpacing(16)
        self.v_pitch = self._metric(hbl, "metric.pitch")
        self.v_yaw = self._metric(hbl, "metric.yaw")
        self.v_roll = self._metric(hbl, "metric.roll")
        self.v_face = self._metric(hbl, "metric.face")

        # 底部居中: 手势结果提示
        self.toast = QLabel("")
        self.toast.setObjectName("GestureToast")
        self.toast.setAlignment(Qt.AlignCenter)
        self.toast.setWordWrap(True)
        self.toast.setVisible(False)

        # 无人脸遮罩 (防偷窥演示)
        self.no_face = QLabel(i18n.t("noface.mask"))
        self.no_face.setObjectName("NoFaceMask")
        self.no_face.setAlignment(Qt.AlignCenter)
        self.no_face.setVisible(False)

        ov.addWidget(self.hud_tl, 0, 0, Qt.AlignLeft | Qt.AlignTop)
        ov.addWidget(self.hud_tr, 0, 1, Qt.AlignRight | Qt.AlignTop)
        ov.addWidget(self.hud_bl, 2, 0, Qt.AlignLeft | Qt.AlignBottom)
        ov.addWidget(self.toast, 2, 0, 1, 2, Qt.AlignHCenter | Qt.AlignBottom)
        ov.addWidget(self.no_face, 0, 0, 3, 2)

        grid.addWidget(overlay, 0, 0)
        return frame

    def _metric(self, layout, key):
        cell = QVBoxLayout()
        cell.setSpacing(1)
        s = QLabel(i18n.t(key))
        s.setObjectName("MetricSmall")
        v = QLabel("0.0°")
        v.setObjectName("MetricValue")
        cell.addWidget(s)
        cell.addWidget(v)
        layout.addLayout(cell)
        self._metric_small.append((s, key))
        return v

    # ------------------------------------------------------------------
    def _build_side_col(self):
        col = QWidget()
        col.setFixedWidth(300)
        v = QVBoxLayout(col)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(14)

        v.addWidget(self._build_gesture_panel())
        v.addWidget(self._build_log_panel(), 1)
        v.addWidget(self._build_sys_panel())
        return col

    def _panel_title(self, parent, key):
        tl = QLabel(i18n.t(key))
        tl.setObjectName("PanelTitle")
        parent.addWidget(tl)
        self._panel_titles.append((tl, key))

    def _build_gesture_panel(self):
        panel = QWidget()
        panel.setObjectName("Panel")
        panel.setAttribute(Qt.WA_StyledBackground, True)
        v = QVBoxLayout(panel)
        v.setContentsMargins(16, 14, 16, 14)
        v.setSpacing(10)
        self._panel_title(v, "panel.gesture")

        self._gesture_widgets = {}
        for key, name_key in GESTURE_ROWS:
            row = QWidget()
            r = QHBoxLayout(row)
            r.setContentsMargins(0, 0, 0, 0)
            r.setSpacing(8)
            name_lbl = QLabel(i18n.t(name_key))
            name_lbl.setObjectName("GestureName")
            name_lbl.setFixedWidth(62)
            bar = QProgressBar()
            bar.setObjectName("GestureBar")
            bar.setTextVisible(False)
            bar.setRange(0, 100)
            bar.setValue(0)
            val = QLabel(i18n.t("stat.count", n=0))
            val.setObjectName("GestureVal")
            val.setFixedWidth(40)
            val.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            r.addWidget(name_lbl)
            r.addWidget(bar, 1)
            r.addWidget(val)
            v.addWidget(row)
            self._gesture_widgets[key] = (bar, val)
            self._gesture_row_names.append((name_lbl, name_key))

        self.gesture_total = QLabel(i18n.t("stat.total", n=0))
        self.gesture_total.setObjectName("GestureVal")
        self.gesture_total.setAlignment(Qt.AlignRight)
        v.addWidget(self.gesture_total)
        return panel

    def _build_log_panel(self):
        panel = QWidget()
        panel.setObjectName("Panel")
        panel.setAttribute(Qt.WA_StyledBackground, True)
        v = QVBoxLayout(panel)
        v.setContentsMargins(16, 14, 16, 14)
        v.setSpacing(8)
        self._panel_title(v, "panel.log")

        self.log_list = QTextEdit()
        self.log_list.setObjectName("LogList")
        self.log_list.setReadOnly(True)
        self.log_list.setFrameShape(QFrame.NoFrame)
        v.addWidget(self.log_list, 1)
        return panel

    def _build_sys_panel(self):
        panel = QWidget()
        panel.setObjectName("Panel")
        panel.setAttribute(Qt.WA_StyledBackground, True)
        v = QVBoxLayout(panel)
        v.setContentsMargins(16, 14, 16, 14)
        v.setSpacing(8)
        self._panel_title(v, "panel.sys")

        _, self.sys_mode = self._sys_row(v, "sys.mode", "sys.menu")
        _, self.sys_model_val = self._sys_row(v, "sys.model")
        self.sys_model_val.setText("MediaPipe FaceMesh")
        _, self.sys_debounce_val = self._sys_row(v, "sys.debounce", "sys.debounce.val")

        self.privacy_note = QLabel(i18n.t("privacy.note"))
        self.privacy_note.setObjectName("PrivacyNote")
        self.privacy_note.setWordWrap(True)
        v.addWidget(self.privacy_note)
        return panel

    def _sys_row(self, parent, k_key, v_key=None):
        row = QWidget()
        r = QHBoxLayout(row)
        r.setContentsMargins(0, 0, 0, 0)
        kk = QLabel(i18n.t(k_key))
        kk.setObjectName("SysKey")
        vv = QLabel(i18n.t(v_key) if v_key else "")
        vv.setObjectName("SysVal")
        r.addWidget(kk)
        r.addStretch(1)
        r.addWidget(vv)
        parent.addWidget(row)
        self._sys_rows.append((kk, k_key, vv, v_key))
        return kk, vv

    def _build_hintbar(self):
        bar = QWidget()
        hb = QHBoxLayout(bar)
        hb.setContentsMargins(0, 0, 0, 0)
        hb.setSpacing(20)
        hb.setAlignment(Qt.AlignCenter)
        for key_key, text_key in [
            ("gesture.nod", "hint.item_nod"),
            ("gesture.nod_up", "hint.item_up"),
            ("gesture.shake_both", "hint.item_shake"),
            ("gesture.mouth_open", "hint.item_mouth"),
        ]:
            box = QWidget()
            b = QHBoxLayout(box)
            b.setContentsMargins(0, 0, 0, 0)
            b.setSpacing(6)
            k = QLabel(i18n.t(key_key))
            k.setObjectName("HintKey")
            t = QLabel(i18n.t(text_key))
            t.setObjectName("HintItem")
            b.addWidget(k)
            b.addWidget(t)
            hb.addWidget(box)
            self._hint_items.append((k, key_key, t, text_key))
        return bar

    # ------------------------------------------------------------------
    def on_frame(self, payload):
        if "error" in payload:
            self.toast.setText(payload["error"])
            self.toast.setVisible(True)
            self._append_logs(payload.get("logs", []))
            return

        img = payload["image"]
        step = payload["step"]
        self.video.set_image(img)
        self._apply_state(step.is_menu)

        # 卡片选中高亮 + 防偷窥开关
        for i, card in enumerate(self.cards):
            active = (i == step.menu_index) and step.is_menu
            card.setProperty("active", active)
            card.style().unpolish(card)
            card.style().polish(card)
        if self.use_tag is not None:
            self.use_tag.setVisible(step.is_menu and step.menu_index == 0)
        self.guard_toggle.set_on(step.anti_peep)
        self.guard_toggle_label.setText(
            i18n.t("toggle.on" if step.anti_peep else "toggle.off"))

        # 标题栏状态
        self.guard_pill.setVisible(step.is_menu and step.anti_peep)

        # 视频 HUD 遥测
        t = T.get_tokens()
        self.hud_tr.setText(
            f"FPS <span style='color:{t['TEXT_PRIMARY']}'>{step.fps}</span>"
            f"&nbsp;| {i18n.t('hud.latency')} "
            f"<span style='color:{t['TEXT_PRIMARY']}'>{step.latency_ms}ms</span>")
        self.v_pitch.setText(f"{step.pitch}°")
        self.v_yaw.setText(f"{step.yaw}°")
        self.v_roll.setText(f"{step.roll}°")
        if step.face_present:
            self.v_face.setText("FACE_OK")
            self.v_face.setStyleSheet(f"color:{t['GREEN']}")
        else:
            self.v_face.setText("NO_FACE")
            self.v_face.setStyleSheet(f"color:{t['RED']}")

        # 无人脸遮罩
        self.no_face.setVisible(step.hidden)

        # 手势提示 toast (离散动作优先, 其次无人脸提示)
        tip = step.bubble or step.continuous
        if not tip and not step.face_present:
            tip = i18n.t("noface.tip")
        self.toast.setText(tip)
        self.toast.setVisible(bool(tip))

        # 动作统计
        stats = step.stats
        max_n = max(stats.values()) if stats else 1
        for key, (bar, val) in self._gesture_widgets.items():
            n = stats.get(key, 0)
            bar.setValue(int(round(n / max_n * 100)) if max_n else 0)
            val.setText(i18n.t("stat.count", n=n))
        self.gesture_total.setText(i18n.t("stat.total", n=sum(stats.values())))

        # 运行模式
        self.sys_mode.setText(mode_name(step.mode) or i18n.t("sys.menu"))

        # 日志
        self._append_logs(payload.get("logs", []))

    # ------------------------------------------------------------------
    def _append_logs(self, logs):
        if not logs:
            return
        for ts, msg, level in logs:
            self._logs.append((ts, msg, level))
        self._render_logs()

    def _render_logs(self):
        t = T.get_tokens()
        colors = _log_colors()
        parts = []
        for ts, msg, level in list(self._logs):
            color = colors.get(level, t["TEXT_SECONDARY"])
            parts.append(
                f'<div style="margin-bottom:6px">'
                f'<span style="color:{t["TEXT_TERTIARY"]}">{html.escape(ts)}</span> '
                f'<span style="color:{color}">{html.escape(msg)}</span></div>')
        self.log_list.setHtml("".join(parts))
        self.log_list.verticalScrollBar().setValue(0)

    # ------------------------------------------------------------------
    def _apply_state(self, is_menu):
        if is_menu == self._last_is_menu:
            return
        self._last_is_menu = is_menu
        self.side_col.setVisible(is_menu)
        self.menu_bar.setVisible(is_menu)
        self.hint_bar.setVisible(is_menu)
        # 小窗模式仅保留视频预览与识别提示, 隐藏遥测 HUD
        self.hud_tl.setVisible(is_menu)
        self.hud_tr.setVisible(is_menu)
        self.hud_bl.setVisible(is_menu)
        # 小窗模式隐藏标题栏冗余元素, 仅保留 返回 / 关闭 按钮
        self.logo.setVisible(is_menu)
        self.app_title.setVisible(is_menu)
        self.title_sub.setVisible(is_menu)
        self.camera_pill.setVisible(is_menu)
        self.guard_pill.setVisible(False)
        self.theme_btn.setVisible(is_menu)
        self.lang_btn.setVisible(is_menu)
        self.min_btn.setVisible(is_menu)
        self.max_btn.setVisible(is_menu)
        self.return_btn.setVisible(not is_menu)
        if is_menu:
            self.setWindowOpacity(1.0)
            self.resize(*MENU_SIZE)
            self._center()
        else:
            self.setWindowOpacity(0.88)
            self.resize(*ACTIVE_SIZE)
            self._corner()

    def _center(self):
        s = QGuiApplication.primaryScreen().availableGeometry()
        self.move(s.x() + (s.width() - self.width()) // 2,
                  s.y() + (s.height() - self.height()) // 2)

    def _corner(self):
        s = QGuiApplication.primaryScreen().availableGeometry()
        self.move(s.x() + s.width() - self.width() - 24,
                  s.y() + s.height() - self.height() - 24)

    def closeEvent(self, _):
        self.thread.stop()
        self.engine.close()