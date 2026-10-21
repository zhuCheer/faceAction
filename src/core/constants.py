"""全局常量：几何索引、检测阈值、行为模式定义。"""

# ---------------------------------------------------------------------------
# MediaPipe FaceMesh 关键点索引 (官方 FACEMESH 约定)
# ---------------------------------------------------------------------------
LEFT_EYE_IDX = [33, 160, 158, 133, 153, 144]
RIGHT_EYE_IDX = [362, 385, 387, 263, 373, 380]
MOUTH_TOP = 13
MOUTH_BOTTOM = 14
MOUTH_LEFT = 61
MOUTH_RIGHT = 291
NOSE_TIP = 1
# 用于估算位姿的脸宽参考点 (左/右脸颊)
LEFT_CHEEK = 234
RIGHT_CHEEK = 454

# 同时检测的人脸数量上限: 2 即可区分「0 / 1 / 多于1」张脸 (供防偷窥多脸检测)
MAX_NUM_FACES = 2

# ---------------------------------------------------------------------------
# 检测阈值 (与 demo 保持一致, 便于对照与调优)
# ---------------------------------------------------------------------------
EAR_BLINK_THRESHOLD = 0.20
EAR_OPEN_THRESHOLD = 0.24
BLINK_MIN_FRAMES = 2
DOUBLE_BLINK_WINDOW_FRAMES = 10
LONG_BLINK_FRAMES = 30
WINK_MIN_FRAMES = 3
WINK_COOLDOWN_FRAMES = 25
MAR_OPEN_THRESHOLD = 0.40
MOUTH_HOLD_FRAMES = 3
MAR_COOLDOWN_FRAMES = 25
TILT_ROLL_THRESHOLD = 0.20
TILT_COOLDOWN_FRAMES = 45
PITCH_NOD_THRESHOLD = 0.15
SHAKE_YAW_THRESHOLD = 0.25
NOD_SHAKE_WINDOW = 30
NOD_SHAKE_COOLDOWN_FRAMES = 45
HEAD_MOVE_YAW_DEADZONE = 0.12
HEAD_MOVE_PITCH_DEADZONE = 0.10
HEAD_MOVE_SMOOTH = 0.10

# 鼠标移动: 头部连续偏移 -> 光标速度 (丝滑比例移动)
MOUSE_SMOOTH = 0.35    # 目标速度低通系数 (越小越平滑)
MOUSE_GAIN = 5.0       # 偏移 -> 速度的软饱和增益 (越大越灵敏)

# 二级操作返回: 需连续张嘴 N 次才返回选择态 (降低误触)
MOUTH_RETURN_COUNT = 2      # 连续张嘴次数阈值
MOUTH_RETURN_WINDOW = 2.5   # 两次张嘴间隔超过该秒数则重置连续计数

# 看抖音模式: 进入即打开该网址
DOUYIN_URL = "https://www.douyin.com/"

# 交互节奏
BUBBLE_HOLD_SECONDS = 1.0

# 防偷窥策略 (非对称防抖):
# - 最小化 (人脸离开): 若正在刷抖音，立即触发，无延时 (隐私优先，尽快最小化)。
# - 恢复 (人脸回归): 需连续稳定该时长，期间任何波动都会重置计时，避免页面闪烁。
ANTI_PEEP_RESTORE_DEBOUNCE_SECONDS = 0.8

# ---------------------------------------------------------------------------
# 行为模式 (一级指令) 定义
# ---------------------------------------------------------------------------
# (mode_id, 菜单显示名 i18n key)
BEHAVIORS = [
    ("douyin", "behavior.douyin"),
    ("anti_peep", "behavior.anti_peep"),
]

# 各模式内「动作 -> 提示文案 i18n key」; 未列出的动作在该模式内被忽略(误判不生效)。
# 张嘴(mouth_open) 已作为全局「返回选择态」手势, 不再出现在任何模式内。
MODE_ACTIONS = {
    "douyin": {
        "nod": "action.nod",
        "nod_up": "action.nod_up",
        "double_blink": "action.double_blink",
    },
}

# 各模式的常驻操作提示 i18n key (展示在悬浮条)
MODE_HINTS = {
    "douyin": "hint.douyin",
    "anti_peep": "hint.anti_peep",
}