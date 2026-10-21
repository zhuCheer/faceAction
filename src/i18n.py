"""多语言支持模块：中英双语语言包。

设计要点:
- 默认语言跟随系统 (auto)；系统语言不匹配任何已支持语言时回退英语。
- UI 与核心逻辑统一通过 t(key, **kwargs) 获取文案，避免硬编码。
- 支持 PyInstaller 打包环境 (Windows 使用 UserDefaultUILanguage 判定更可靠)。
"""

# 已支持的语言标识
SUPPORTED_LANGUAGES = ("zh", "en")

# 兜底语言 (不匹配任何语言时使用)
DEFAULT_LANGUAGE = "en"

# 语言名展示 (按钮显示当前语言，始终以该语言自身命名)
LANGUAGE_NAMES = {
    "zh": "中文",
    "en": "English",
}

# ---------------------------------------------------------------------------
# 语言包表
# ---------------------------------------------------------------------------
_STRINGS = {
    "zh": {
        # 窗口 / 标题
        "app_name": "面部行为控制",
        "title_sub": "面部控制助手 v0.5",
        "return_btn": "返回",
        # 语言 / 主题按钮
        "theme_dark": "☾ 深色模式",
        "theme_light": "☀ 亮色模式",
        # 状态气泡
        "camera_connected": "摄像头已连接 · 1080p",
        "guard_on": "防偷窥已开启",
        # 行为模式 (一级指令)
        "behavior.douyin": "看抖音",
        "behavior.anti_peep": "防偷窥",
        # 模式内动作
        "action.nod": "下一个视频",
        "action.nod_up": "上一个视频",
        "action.double_blink": "单击",
        # 常驻提示
        "hint.douyin": "低头下一个 · 抬头一个 · 双眨眼单击 · 连张2次嘴返回",
        "hint.anti_peep": "点头切换开/关 · 开启后离开画面自动切桌面",
        "hint.menu": "右摇→下一项 · 左摇→上一项 · 点头确认/切换 · 防偷窥:{status}",
        # 持续移动状态
        "move.move_left": "光标←",
        "move.move_right": "光标→",
        "move.move_up": "光标↑",
        "move.move_down": "光标↓",
        # 离散气泡
        "bubble.switch": "切换: {name}",
        "bubble.enter": "进入: {name}",
        "bubble.anti_peep_on": "防偷窥: 已开启",
        "bubble.anti_peep_off": "防偷窥: 已关闭",
        "bubble.return": "张嘴×2 → 返回选择",
        "bubble.return_again": "再张嘴一次返回",
        "state.on": "已开启",
        "state.off": "已关闭",
        # 手势名
        "gesture.nod": "点头",
        "gesture.nod_up": "抬头",
        "gesture.shake_left": "左摇",
        "gesture.shake_right": "右摇",
        "gesture.mouth_open": "张嘴×2",
        "gesture.shake_both": "左摇 / 右摇",
        # 模式卡片
        "card.douyin_sub": "点头 → 下一条 · 抬头 → 上一条",
        "card.douyin_kbd": "张嘴×2 返回菜单",
        "card.guard_sub": "人脸离开 → 自动切桌面 · 回归 → 恢复",
        "card.guard_kbd": "点头 切换 开/关",
        # 开关 / 标签
        "toggle.on": "开",
        "toggle.off": "关",
        "use.tag": "选中",
        # 视频 HUD
        "hud.live": "● 实时检测 · FaceMesh 468pts",
        "hud.latency": "延迟",
        "metric.pitch": "PITCH 俯仰",
        "metric.yaw": "YAW 偏航",
        "metric.roll": "ROLL 翻滚",
        "metric.face": "状态",
        "noface.mask": "未检测到人脸 · 已切换到桌面",
        "noface.tip": "未检测到人脸",
        # 侧边面板
        "panel.gesture": "动作识别 · 操作统计",
        "panel.log": "运行日志",
        "panel.sys": "系统状态",
        "sys.mode": "运行模式",
        "sys.menu": "选择态",
        "sys.model": "检测模型",
        "sys.debounce": "防抖策略",
        "sys.debounce.val": "隐藏即时 · 恢复 500ms",
        "privacy.note": "🔒 隐私安全 — 所有画面均在本地离线处理，不上传任何数据。",
        # 底部提示条
        "hint.item_nod": "确认 / 下一条",
        "hint.item_up": "上一条",
        "hint.item_shake": "切换菜单项",
        "hint.item_mouth": "返回选择态",
        # 统计
        "stat.count": "{n}次",
        "stat.total": "共 {n} 次",
        # 运行日志
        "log.boot": "FaceAction 启动完成 v0.5.0",
        "log.facemesh_ready": "FaceMesh 模型加载完成，468 关键点就绪",
        "log.camera_ready": "摄像头就绪 1080p · 30fps",
        "log.camera_error": "无法打开摄像头 (index={index})",
        "log.enter_douyin": "进入看抖音模式，已打开抖音",
        "log.return_menu": "返回选择态",
        "log.anti_peep_on": "防偷窥已开启 — 人脸离开画面立即 Win+D",
        "log.anti_peep_off": "防偷窥已关闭",
        "log.no_face_hide": "no_face 持续 → 已发送 Win+D 切至桌面",
        "log.face_restore": "人脸回归 → 已恢复浏览器窗口",
    },
    "en": {
        "app_name": "Face Action Control",
        "title_sub": "Face Control Assistant v0.5",
        "return_btn": "Back",
        "theme_dark": "☾ Dark Mode",
        "theme_light": "☀ Light Mode",
        "camera_connected": "Camera connected · 1080p",
        "guard_on": "Anti-peep enabled",
        "behavior.douyin": "Watch Douyin",
        "behavior.anti_peep": "Anti-peep",
        "action.nod": "Next video",
        "action.nod_up": "Prev video",
        "action.double_blink": "Click",
        "hint.douyin": "Nod next · look up prev · double blink click · mouth ×2 to return",
        "hint.anti_peep": "Nod to toggle · hide desktop when away",
        "hint.menu": "Shake R→next · Shake L→prev · Nod confirm/toggle · Anti-peep:{status}",
        "move.move_left": "Cursor ←",
        "move.move_right": "Cursor →",
        "move.move_up": "Cursor ↑",
        "move.move_down": "Cursor ↓",
        "bubble.switch": "Switch: {name}",
        "bubble.enter": "Enter: {name}",
        "bubble.anti_peep_on": "Anti-peep: On",
        "bubble.anti_peep_off": "Anti-peep: Off",
        "bubble.return": "Mouth ×2 → back to menu",
        "bubble.return_again": "Open mouth once more to return",
        "state.on": "On",
        "state.off": "Off",
        "gesture.nod": "Nod",
        "gesture.nod_up": "Look up",
        "gesture.shake_left": "Shake L",
        "gesture.shake_right": "Shake R",
        "gesture.mouth_open": "Mouth ×2",
        "gesture.shake_both": "Shake L / R",
        "card.douyin_sub": "Nod → next · look up → prev",
        "card.douyin_kbd": "Mouth ×2 back to menu",
        "card.guard_sub": "Face away → hide desktop · return → restore",
        "card.guard_kbd": "Nod to toggle on/off",
        "toggle.on": "On",
        "toggle.off": "Off",
        "use.tag": "Selected",
        "hud.live": "● Live · FaceMesh 468pts",
        "hud.latency": "Latency",
        "metric.pitch": "PITCH",
        "metric.yaw": "YAW",
        "metric.roll": "ROLL",
        "metric.face": "Status",
        "noface.mask": "No face · switched to desktop",
        "noface.tip": "No face detected",
        "panel.gesture": "Gestures · Stats",
        "panel.log": "Logs",
        "panel.sys": "System",
        "sys.mode": "Mode",
        "sys.menu": "Menu",
        "sys.model": "Model",
        "sys.debounce": "Debounce",
        "sys.debounce.val": "Hide instant · restore 500ms",
        "privacy.note": "🔒 Privacy — all frames are processed locally & offline; no data is uploaded.",
        "hint.item_nod": "Confirm / Next",
        "hint.item_up": "Prev",
        "hint.item_shake": "Switch item",
        "hint.item_mouth": "Back to menu",
        "stat.count": "{n}",
        "stat.total": "Total {n}",
        "log.boot": "FaceAction started v0.5.0",
        "log.facemesh_ready": "FaceMesh model loaded, 468 landmarks ready",
        "log.camera_ready": "Camera ready 1080p · 30fps",
        "log.camera_error": "Cannot open camera (index={index})",
        "log.enter_douyin": "Entered Douyin mode, opened Douyin",
        "log.return_menu": "Returned to menu",
        "log.anti_peep_on": "Anti-peep on — hide desktop when face away",
        "log.anti_peep_off": "Anti-peep off",
        "log.no_face_hide": "No face → Win+D sent to desktop",
        "log.face_restore": "Face restored → browser window restored",
    },
}

# 当前语言设置："auto" 表示跟随系统；否则为 "zh" / "en"
_current = "auto"


# ---------------------------------------------------------------------------
# 系统语言探测
# ---------------------------------------------------------------------------
def _windows_ui_language():
    """优先用 Windows 用户界面语言 (LANGID 主语言) 判定，失败返回空串。"""
    try:
        import ctypes
        langid = ctypes.windll.kernel32.GetUserDefaultUILanguage()
        primary = langid & 0x3FF          # 主语言 ID (低 10 位)
        if primary == 0x04:               # LANG_CHINESE
            return "zh"
        if primary == 0x09:               # LANG_ENGLISH
            return "en"
    except Exception:
        pass
    return ""


def _locale_language():
    """回退：locale.getdefaultlocale / 环境变量 LANG / LC_ALL。"""
    import locale
    import os
    cands = []
    try:
        lang, _ = locale.getdefaultlocale()
        if lang:
            cands.append(lang)
    except Exception:
        pass
    for var in ("LANG", "LC_ALL", "LC_MESSAGES"):
        val = os.environ.get(var)
        if val:
            cands.append(val)
    return "".join(cands)


def resolve_system_language():
    """把系统语言映射到已支持语言；不匹配返回兜底语言 (英语)。"""
    raw = _windows_ui_language() or _locale_language()
    if not raw:
        return DEFAULT_LANGUAGE
    raw = raw.lower().replace("_", "-")
    if raw.startswith("zh"):
        return "zh"
    if raw.startswith("en"):
        return "en"
    return DEFAULT_LANGUAGE


# ---------------------------------------------------------------------------
# 对外接口
# ---------------------------------------------------------------------------
def get_language():
    """返回当前设置 ("auto" / "zh" / "en")。"""
    return _current


def effective_language():
    """返回实际生效语言：auto 时按系统解析，否则直接返回。"""
    if _current == "auto":
        return resolve_system_language()
    return _current if _current in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE


def set_language(lang):
    """设置语言：auto 跟随系统；不匹配任何语言回退英语。"""
    global _current
    if lang == "auto":
        _current = "auto"
    elif lang in SUPPORTED_LANGUAGES:
        _current = lang
    else:
        _current = DEFAULT_LANGUAGE
    return _current


def t(key, **kwargs):
    """取当前语言下 key 的文案，支持 str.format 占位参数。

    未命中 key 时回退英语表，再回退到 key 本身，保证界面不出现空串。
    """
    lang = effective_language()
    table = _STRINGS.get(lang, _STRINGS[DEFAULT_LANGUAGE])
    text = table.get(key)
    if text is None:
        text = _STRINGS[DEFAULT_LANGUAGE].get(key, key)
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, IndexError):
            return text
    return text