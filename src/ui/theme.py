"""玻璃拟态主题配色 (用于 QSS)，支持深色 / 亮色切换。

深色参考 FaceAction-UI-Glassmorphism.html；
亮色参考 FaceAction-UI-Glassmorphism-Light.html (晨空)。
"""
from PySide6.QtGui import QColor, QFont

FONT_FAMILY = "Microsoft YaHei"
MONO_FAMILY = "Consolas"

# 主题令牌
TOKENS = {
    "dark": {
        "WINDOW_BG": ("qlineargradient(x1:0, y1:0, x2:1, y2:1, "
                      "stop:0 rgb(20, 26, 44), stop:1 rgb(12, 16, 28))"),
        "LOGO_GRAD": ("qlineargradient(x1:0, y1:0, x2:1, y2:1, "
                      "stop:0 #25f4ee, stop:1 #fe2c55)"),
        "TOGGLE_ON_GRAD": ("qlineargradient(x1:0, y1:0, x2:1, y2:0, "
                           "stop:0 #25f4ee, stop:1 #34d399)"),
        "CARD_ACTIVE_BG": ("qlineargradient(x1:0, y1:0, x2:1, y2:1, "
                           "stop:0 rgba(37, 244, 238, 0.10), stop:1 rgba(254, 44, 85, 0.10))"),
        "TEXT_PRIMARY": "#f5f7fa",
        "TEXT_SECONDARY": "#aeb6cc",
        "TEXT_TERTIARY": "#7d8598",
        "ACCENT": "#25f4ee",
        "ACCENT2": "#fe2c55",
        "GREEN": "#34d399",
        "RED": "#fe2c55",
        "GLASS_BG": "rgba(255, 255, 255, 0.055)",
        "GLASS_BG_STRONG": "rgba(255, 255, 255, 0.09)",
        "GLASS_BORDER": "rgba(255, 255, 255, 0.12)",
        "GLASS_BORDER_STRONG": "rgba(255, 255, 255, 0.2)",
        "TAG_FG": "#06121a",
        "CHIP_BG": "rgba(10, 14, 24, 0.55)",
        "TOGGLE_OFF": "rgba(255, 255, 255, 0.12)",
        "NOFACE_BG": "rgba(6, 8, 14, 0.82)",
        "PRIVACY_BG": "rgba(52, 211, 153, 0.06)",
        "PRIVACY_BORDER": "rgba(52, 211, 153, 0.18)",
        "VIDEO_BG": "#0d1220",
    },
    "light": {
        "WINDOW_BG": ("qlineargradient(x1:0, y1:0, x2:1, y2:1, "
                      "stop:0 rgb(255, 255, 255), stop:1 rgb(224, 231, 255))"),
        "LOGO_GRAD": ("qlineargradient(x1:0, y1:0, x2:1, y2:1, "
                      "stop:0 #8b5cf6, stop:1 #6d28d9)"),
        "TOGGLE_ON_GRAD": ("qlineargradient(x1:0, y1:0, x2:1, y2:0, "
                           "stop:0 #8b5cf6, stop:1 #6d28d9)"),
        "CARD_ACTIVE_BG": ("qlineargradient(x1:0, y1:0, x2:1, y2:1, "
                           "stop:0 rgba(255, 255, 255, 0.72), stop:1 rgba(196, 181, 253, 0.35))"),
        "TEXT_PRIMARY": "#1e1b4b",
        "TEXT_SECONDARY": "rgba(30, 27, 75, 0.70)",
        "TEXT_TERTIARY": "rgba(30, 27, 75, 0.35)",
        "ACCENT": "#6d28d9",
        "ACCENT2": "#8b5cf6",
        "GREEN": "#059669",
        "RED": "#e11d48",
        "GLASS_BG": "rgba(255, 255, 255, 0.55)",
        "GLASS_BG_STRONG": "rgba(255, 255, 255, 0.70)",
        "GLASS_BORDER": "rgba(255, 255, 255, 0.70)",
        "GLASS_BORDER_STRONG": "rgba(255, 255, 255, 0.90)",
        "TAG_FG": "#ffffff",
        "CHIP_BG": "rgba(255, 255, 255, 0.78)",
        "TOGGLE_OFF": "rgba(30, 27, 75, 0.14)",
        "NOFACE_BG": "rgba(255, 255, 255, 0.82)",
        "PRIVACY_BG": "rgba(255, 255, 255, 0.45)",
        "PRIVACY_BORDER": "rgba(255, 255, 255, 0.90)",
        "VIDEO_BG": "#1e1b4b",
    },
}

_MODE = "dark"


def get_tokens(mode=None):
    return TOKENS[mode or _MODE]


def get_theme():
    return _MODE


def set_theme(mode):
    global _MODE
    _MODE = "light" if mode == "light" else "dark"
    return _MODE


def _rgba(hex_color, alpha):
    """把 #RRGGBB 转 rgba(r,g,b,a)。"""
    c = QColor(hex_color)
    return f"rgba({c.red()},{c.green()},{c.blue()},{alpha})"


def base_font(size=10, weight=QFont.Normal):
    f = QFont(FONT_FAMILY, size)
    f.setWeight(weight)
    return f


def build_stylesheet(mode=None) -> str:
    t = get_tokens(mode)
    P, S, Tt = t["TEXT_PRIMARY"], t["TEXT_SECONDARY"], t["TEXT_TERTIARY"]
    A, A2 = t["ACCENT"], t["ACCENT2"]
    G, R = t["GREEN"], t["RED"]
    gb, gbs = t["GLASS_BG"], t["GLASS_BG_STRONG"]
    gbr, gbrs = t["GLASS_BORDER"], t["GLASS_BORDER_STRONG"]
    fg, chip = t["TAG_FG"], t["CHIP_BG"]
    accent45 = _rgba(A, 0.45)
    accent35 = _rgba(A, 0.35)

    return f"""
    /* ===== 根窗口 (无边框透明, 由内层绘制玻璃圆角) ===== */
    QWidget#Root {{
        background: transparent;
    }}
    QWidget#GlassWindow {{
        background: {t["WINDOW_BG"]};
        border: 1px solid {gbrs};
        border-radius: 16px;
    }}

    /* ===== 标题栏 ===== */
    QWidget#TitleBar {{
        background: transparent;
        border-bottom: 1px solid {gbr};
    }}
    QLabel#Logo {{
        background: {t["LOGO_GRAD"]};
        border-radius: 8px;
        color: {fg};
        font-family: "{FONT_FAMILY}";
        font-size: 12px;
        font-weight: bold;
    }}
    QLabel#Title {{
        color: {P};
        font-family: "{FONT_FAMILY}";
        font-size: 13px;
        font-weight: 600;
    }}
    QLabel#TitleSub {{
        color: {Tt};
        font-family: "{FONT_FAMILY}";
        font-size: 12px;
    }}
    QLabel#StatusPill {{
        color: {S};
        background: {gb};
        border: 1px solid {gbr};
        border-radius: 20px;
        padding: 4px 10px;
        font-family: "{FONT_FAMILY}";
        font-size: 11px;
    }}
    QPushButton#ThemeBtn, QPushButton#LangBtn {{
        color: {S};
        background: {gb};
        border: 1px solid {gbr};
        border-radius: 20px;
        padding: 4px 10px;
        font-family: "{FONT_FAMILY}";
        font-size: 11px;
    }}
    QPushButton#ThemeBtn:hover, QPushButton#LangBtn:hover {{
        background: {gbs};
        color: {P};
    }}
    QLabel#DotLive {{
        background: {G};
        border-radius: 6px;
        min-width: 6px; max-width: 6px;
        min-height: 6px; max-height: 6px;
    }}
    QLabel#DotGuard {{
        background: {A};
        border-radius: 6px;
        min-width: 6px; max-width: 6px;
        min-height: 6px; max-height: 6px;
    }}

    /* 窗口控制按钮 */
    QPushButton#WinButton {{
        background: transparent;
        color: {S};
        border: none;
        font-family: "{FONT_FAMILY}";
        font-size: 13px;
    }}
    QPushButton#WinButton:hover {{
        background: {gbs};
        color: {P};
    }}
    QPushButton#WinClose {{
        background: transparent;
        color: {S};
        border: none;
        font-family: "{FONT_FAMILY}";
        font-size: 13px;
    }}
    QPushButton#WinClose:hover {{
        background: #e81123;
        color: #ffffff;
    }}

    /* ===== 视频预览 ===== */
    QFrame#VideoFrame {{
        background: {t["VIDEO_BG"]};
        border: 1px solid {gbr};
        border-radius: 14px;
    }}
    QLabel#Hud {{
        color: {S};
        background: {chip};
        border: 1px solid {gbr};
        border-radius: 8px;
        padding: 6px 12px;
        font-family: "{FONT_FAMILY}";
        font-size: 11px;
    }}
    QLabel#HudMono {{
        color: {S};
        background: {chip};
        border: 1px solid {gbr};
        border-radius: 8px;
        padding: 6px 12px;
        font-family: "{MONO_FAMILY}";
        font-size: 11px;
    }}
    QLabel#MetricSmall {{
        color: {Tt};
        font-family: "{FONT_FAMILY}";
        font-size: 9px;
    }}
    QLabel#MetricValue {{
        color: {P};
        font-family: "{MONO_FAMILY}";
        font-size: 12px;
        font-weight: 600;
    }}
    QWidget#HudBox {{
        background: {chip};
        border: 1px solid {gbr};
        border-radius: 8px;
    }}
    QLabel#GestureToast {{
        color: {P};
        background: {chip};
        border: 1px solid {accent35};
        border-radius: 12px;
        padding: 10px 18px;
        font-family: "{FONT_FAMILY}";
        font-size: 13px;
    }}
    QLabel#NoFaceMask {{
        color: {P};
        background: {t["NOFACE_BG"]};
        border-radius: 14px;
        font-family: "{FONT_FAMILY}";
        font-size: 15px;
        font-weight: 600;
    }}

    /* ===== 模式卡片 ===== */
    QWidget#MenuCard {{
        background: {gb};
        border: 1px solid {gbr};
        border-radius: 14px;
    }}
    QWidget#MenuCard[active="true"] {{
        background: {t["CARD_ACTIVE_BG"]};
        border: 1px solid {accent45};
    }}
    QLabel#CardIcon {{
        background: {gbs};
        border: 1px solid {gbr};
        border-radius: 14px;
        color: {A};
        font-family: "{FONT_FAMILY}";
        font-size: 22px;
        font-weight: bold;
    }}
    QLabel#CardTitle {{
        color: {P};
        font-family: "{FONT_FAMILY}";
        font-size: 16px;
        font-weight: 700;
    }}
    QLabel#CardSub {{
        color: {S};
        font-family: "{FONT_FAMILY}";
        font-size: 12px;
    }}
    QLabel#CardKbd {{
        color: {Tt};
        font-family: "{MONO_FAMILY}";
        font-size: 10px;
    }}
    QLabel#UseTag {{
        color: {fg};
        background: {A};
        border-radius: 10px;
        padding: 3px 9px;
        font-family: "{FONT_FAMILY}";
        font-size: 10px;
        font-weight: 600;
    }}
    /* 防偷窥开关 */
    QLabel#ToggleLabel {{
        color: {S};
        font-family: "{FONT_FAMILY}";
        font-size: 11px;
        font-weight: 600;
    }}
    QWidget#Toggle {{
        background: {t["TOGGLE_OFF"]};
        border: 1px solid {gbr};
        border-radius: 14px;
    }}
    QWidget#Toggle[on="true"] {{
        background: {t["TOGGLE_ON_GRAD"]};
        border: 1px solid transparent;
    }}
    QWidget#Toggle QLabel#ToggleKnob {{
        background: #ffffff;
        border-radius: 10px;
    }}

    /* ===== 右侧面板 ===== */
    QWidget#Panel {{
        background: {gb};
        border: 1px solid {gbr};
        border-radius: 14px;
    }}
    QLabel#PanelTitle {{
        color: {Tt};
        font-family: "{FONT_FAMILY}";
        font-size: 11px;
        font-weight: 700;
    }}
    QLabel#GestureName {{
        color: {S};
        font-family: "{FONT_FAMILY}";
        font-size: 12px;
    }}
    QLabel#GestureVal {{
        color: {Tt};
        font-family: "{MONO_FAMILY}";
        font-size: 11px;
    }}
    QProgressBar#GestureBar {{
        background: rgba(0, 0, 0, 0.12);
        border: none;
        border-radius: 2px;
        min-height: 6px;
        max-height: 6px;
    }}
    QProgressBar#GestureBar::chunk {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {A}, stop:1 {A2});
        border-radius: 2px;
    }}

    /* 日志 */
    QTextEdit#LogList {{
        background: transparent;
        color: {S};
        border: none;
        font-family: "{MONO_FAMILY}";
        font-size: 11px;
    }}

    /* 系统状态 */
    QLabel#SysKey {{
        color: {Tt};
        font-family: "{FONT_FAMILY}";
        font-size: 12px;
    }}
    QLabel#SysVal {{
        color: {S};
        font-family: "{MONO_FAMILY}";
        font-size: 12px;
    }}
    QLabel#PrivacyNote {{
        color: {Tt};
        background: {t["PRIVACY_BG"]};
        border: 1px solid {t["PRIVACY_BORDER"]};
        border-radius: 10px;
        padding: 10px 12px;
        font-family: "{FONT_FAMILY}";
        font-size: 11px;
    }}

    /* 底部提示 */
    QLabel#HintItem {{
        color: {Tt};
        font-family: "{FONT_FAMILY}";
        font-size: 11px;
    }}
    QLabel#HintKey {{
        color: {S};
        background: {gb};
        border: 1px solid {gbr};
        border-radius: 6px;
        padding: 2px 7px;
        font-family: "{MONO_FAMILY}";
        font-size: 10px;
    }}
    """