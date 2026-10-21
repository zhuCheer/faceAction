"""指令执行器：通过 Windows SendInput 发送鼠标/键盘事件，浏览器用默认浏览器打开。

零第三方输入库依赖 (仅 ctypes + webbrowser)。
"""
import ctypes
import webbrowser
from ctypes import wintypes

from .mapper import Command

# ---------------------------------------------------------------------------
# SendInput 结构
# ---------------------------------------------------------------------------
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_WHEEL = 0x0800
KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002
INPUT_MOUSE = 0
INPUT_KEYBOARD = 1
WHEEL_DELTA = 120

# 键名 -> (虚拟键码, 是否为扩展键)
KEYMAP = {
    "LEFT": (0x25, True),
    "UP": (0x26, True),
    "RIGHT": (0x27, True),
    "DOWN": (0x28, True),
    "PAGE_UP": (0x21, True),
    "PAGE_DOWN": (0x22, True),
    "ENTER": (0x0D, False),
    "ESC": (0x1B, False),
    "TAB": (0x09, False),
    "VOL_DOWN": (0xAE, True),
    "VOL_UP": (0xAF, True),
    "MEDIA_NEXT": (0xB0, True),
    "MEDIA_PREV": (0xB1, True),
    "MEDIA_PLAY_PAUSE": (0xB3, True),
}

_ULONG_PTR = ctypes.POINTER(ctypes.c_ulong)


class _MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG), ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD), ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD), ("dwExtraInfo", _ULONG_PTR),
    ]


class _KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD), ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD), ("time", wintypes.DWORD),
        ("dwExtraInfo", _ULONG_PTR),
    ]


class _INPUTUNION(ctypes.Union):
    _fields_ = [("mi", _MOUSEINPUT), ("ki", _KEYBDINPUT)]


class _INPUT(ctypes.Structure):
    _fields_ = [("type", wintypes.DWORD), ("union", _INPUTUNION)]


def _mouse(flags, dx=0, dy=0, data=0):
    i = _INPUT()
    i.type = INPUT_MOUSE
    i.union.mi.dx = dx
    i.union.mi.dy = dy
    i.union.mi.mouseData = data
    i.union.mi.dwFlags = flags
    return i


def _key(vk, up=False, extended=False):
    i = _INPUT()
    i.type = INPUT_KEYBOARD
    i.union.ki.wVk = vk
    flags = KEYEVENTF_KEYUP if up else 0
    if extended:
        flags |= KEYEVENTF_EXTENDEDKEY
    i.union.ki.dwFlags = flags
    return i


def _send(*inputs):
    n = len(inputs)
    arr = (_INPUT * n)(*inputs)
    ctypes.windll.user32.SendInput(n, arr, ctypes.sizeof(_INPUT))


# ---------------------------------------------------------------------------
# 窗口管理: 防偷窥恢复时把浏览器窗体重新激活到最前
# ---------------------------------------------------------------------------
_user32 = ctypes.windll.user32
_kernel32 = ctypes.windll.kernel32

# 常见浏览器进程名 (小写)，用于定位浏览器主窗口
BROWSER_PROCS = {
    "chrome.exe", "msedge.exe", "firefox.exe", "iexplore.exe", "opera.exe",
    "brave.exe", "360se.exe", "360chrome.exe", "qqbrowser.exe",
    "sogouexplorer.exe", "maxthon.exe", "ucbrowser.exe",
}

_SW_MAXIMIZE = 3
_PROCESS_QUERY_LIMITED_INFORMATION = 0x1000


def _process_name(pid):
    """由进程 ID 获取可执行文件名 (小写)，失败返回空串。"""
    _kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    _kernel32.OpenProcess.restype = wintypes.HANDLE
    _kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    # QueryFullProcessImageNameW 位于 kernel32.dll
    _kernel32.QueryFullProcessImageNameW.argtypes = [
        wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
    _kernel32.QueryFullProcessImageNameW.restype = wintypes.BOOL

    h = _kernel32.OpenProcess(_PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not h:
        return ""
    try:
        buf = ctypes.create_unicode_buffer(260)
        size = wintypes.DWORD(260)
        if _kernel32.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(size)):
            return buf.value.rsplit("\\", 1)[-1].lower()
    finally:
        _kernel32.CloseHandle(h)
    return ""


def _find_browser_window():
    """枚举可见顶层窗口，返回第一个带标题的浏览器窗口句柄；找不到返回 None。"""
    _user32.IsWindowVisible.argtypes = [wintypes.HWND]
    _user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
    _user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]

    found = []
    _EnumProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    def _cb(hwnd, _lparam):
        if not _user32.IsWindowVisible(hwnd):
            return True
        if _user32.GetWindowTextLengthW(hwnd) == 0:
            return True
        pid = wintypes.DWORD()
        _user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if _process_name(pid.value) in BROWSER_PROCS:
            found.append(hwnd)
            return False  # 已找到，停止枚举
        return True

    _user32.EnumWindows(_EnumProc(_cb), 0)
    return found[0] if found else None


def _activate_window(hwnd):
    """恢复并最大化目标窗口，激活到最前（用 Alt 键绕开前台锁定限制）。"""
    if not hwnd:
        return
    _user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
    _user32.SetForegroundWindow.argtypes = [wintypes.HWND]
    _user32.BringWindowToTop.argtypes = [wintypes.HWND]

    # SW_RESTORE 会退回普通大小，这里直接 SW_MAXIMIZE 保证浏览器满屏
    _user32.ShowWindow(hwnd, _SW_MAXIMIZE)
    # 先模拟一次 Alt 键，解除 Windows 的前台锁定
    _user32.keybd_event(0x12, 0, 0, 0)                # Alt down
    _user32.keybd_event(0x12, 0, KEYEVENTF_KEYUP, 0)  # Alt up
    _user32.SetForegroundWindow(hwnd)
    _user32.BringWindowToTop(hwnd)


class Executor:
    def __init__(self):
        self._held_key = None   # 方向键模式当前按住的键名
        self._mouse_down = False  # 拖拽状态
        self.browser_opened = False  # 是否已通过本执行器打开过浏览器

    # ------------------------------------------------------------------
    def execute(self, cmd: Command or None):
        if cmd is None:
            return
        if cmd.kind == "mouse":
            self._run_mouse(cmd.action)
        elif cmd.kind == "key":
            self.key_tap(cmd.key)
        elif cmd.kind == "browser":
            self.open_url(cmd.url)

    def _run_mouse(self, action):
        if action == "click":
            self.mouse_click()
        elif action == "double_click":
            self.mouse_double_click()
        elif action == "drag_toggle":
            self.mouse_drag_toggle()
        elif action == "wheel_up":
            self.scroll_wheel(down=False)
        elif action == "wheel_down":
            self.scroll_wheel(down=True)
        elif action == "center":
            self.center_cursor()

    # ------------------------------------------------------------------
    def center_cursor(self):
        """把光标移动到主屏中心 (丢失光标时找回)。"""
        user32 = ctypes.windll.user32
        w = user32.GetSystemMetrics(0)   # SM_CXSCREEN
        h = user32.GetSystemMetrics(1)   # SM_CYSCREEN
        user32.SetCursorPos(w // 2, h // 2)

    def mouse_move_rel(self, dx, dy):
        _send(_mouse(MOUSEEVENTF_MOVE, dx, dy))

    def mouse_click(self):
        _send(_mouse(MOUSEEVENTF_LEFTDOWN), _mouse(MOUSEEVENTF_LEFTUP))

    def mouse_double_click(self):
        self.mouse_click()
        self.mouse_click()

    def mouse_drag_toggle(self):
        if self._mouse_down:
            _send(_mouse(MOUSEEVENTF_LEFTUP))
            self._mouse_down = False
        else:
            _send(_mouse(MOUSEEVENTF_LEFTDOWN))
            self._mouse_down = True

    def scroll_wheel(self, down=True, amount=1):
        data = -WHEEL_DELTA * amount if down else WHEEL_DELTA * amount
        _send(_mouse(MOUSEEVENTF_WHEEL, data=data))

    # ------------------------------------------------------------------
    def key_tap(self, name):
        if name not in KEYMAP:
            return
        vk, ext = KEYMAP[name]
        _send(_key(vk, extended=ext), _key(vk, up=True, extended=ext))

    def key_down(self, name):
        if name not in KEYMAP:
            return
        vk, ext = KEYMAP[name]
        _send(_key(vk, extended=ext))

    def key_up(self, name):
        if name not in KEYMAP:
            return
        vk, ext = KEYMAP[name]
        _send(_key(vk, up=True, extended=ext))

    # 方向键持续按住管理
    def hold_direction(self, direction):
        """direction: move_left/move_right/move_up/move_down; 切换按住对应方向键。"""
        arrow = {
            "move_left": "LEFT", "move_right": "RIGHT",
            "move_up": "UP", "move_down": "DOWN",
        }.get(direction)
        if arrow == self._held_key:
            return
        if self._held_key:
            self.key_up(self._held_key)
        if arrow:
            self.key_down(arrow)
        self._held_key = arrow

    def release_direction(self):
        if self._held_key:
            self.key_up(self._held_key)
            self._held_key = None

    # ------------------------------------------------------------------
    def open_url(self, url):
        if url:
            webbrowser.open(url)
            self.browser_opened = True

    def show_desktop(self):
        """直接发送 Win+D：将所有窗体收起（显示桌面），再次发送则恢复。"""
        user32 = ctypes.windll.user32
        KEYEVENTF_KEYUP = 0x0002
        user32.keybd_event(0x5B, 0, 0, 0)               # 左 Win 按下
        user32.keybd_event(0x44, 0, 0, 0)               # D 按下
        user32.keybd_event(0x44, 0, KEYEVENTF_KEYUP, 0)  # D 抬起
        user32.keybd_event(0x5B, 0, KEYEVENTF_KEYUP, 0)  # 左 Win 抬起

    def restore_douyin(self, url):
        """防偷窥恢复：已开过浏览器则 Win+D 恢复，否则打开抖音；最后把浏览器激活到最前。"""
        if self.browser_opened:
            self.show_desktop()
        else:
            self.open_url(url)
        # 恢复/打开后，浏览器可能落在其它窗体后面，这里显式把它置于最前
        _activate_window(_find_browser_window())

    def release_all(self):
        """退出/重置时释放所有按住状态。"""
        self.release_direction()
        if self._mouse_down:
            _send(_mouse(MOUSEEVENTF_LEFTUP))
            self._mouse_down = False