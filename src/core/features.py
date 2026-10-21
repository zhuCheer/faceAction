"""特征提取：基于 468 关键点计算 EAR / MAR / pitch / yaw / roll 与移动方向。

本模块为纯函数层，不持有状态，便于单元测试。
"""
from dataclasses import dataclass
import math

import numpy as np

from .constants import (
    LEFT_EYE_IDX,
    RIGHT_EYE_IDX,
    MOUTH_TOP,
    MOUTH_BOTTOM,
    MOUTH_LEFT,
    MOUTH_RIGHT,
    NOSE_TIP,
    LEFT_CHEEK,
    RIGHT_CHEEK,
)


@dataclass
class Features:
    ear: float
    ear_left: float
    ear_right: float
    mar: float
    pitch: float
    yaw: float
    roll: float


def eye_aspect_ratio(landmarks, idx):
    """眼睛纵横比 EAR: (||p2-p6|| + ||p3-p5||) / (2 * ||p1-p4||)。"""
    p1, p2, p3, p4, p5, p6 = (landmarks[i] for i in idx)
    a = np.linalg.norm(np.array(p2) - np.array(p6))
    b = np.linalg.norm(np.array(p3) - np.array(p5))
    c = np.linalg.norm(np.array(p1) - np.array(p4))
    return (a + b) / (2.0 * c + 1e-6)


def mouth_aspect_ratio(landmarks):
    """嘴部纵横比 MAR: 上下唇距离 / 嘴角宽度。"""
    top = np.array(landmarks[MOUTH_TOP])
    bottom = np.array(landmarks[MOUTH_BOTTOM])
    left = np.array(landmarks[MOUTH_LEFT])
    right = np.array(landmarks[MOUTH_RIGHT])
    v = np.linalg.norm(top - bottom)
    h = np.linalg.norm(left - right)
    return v / (h + 1e-6)


def head_pose(landmarks, frame_shape):
    """基于鼻尖相对面宽/画面中心的偏移归一化估算 (pitch, yaw)。

    正值 pitch = 低头, 正值 yaw = 鼻尖相对画面中心右移。
    """
    h, w = frame_shape[:2]
    nose = np.array(landmarks[NOSE_TIP])
    dx = nose[0] - w / 2
    dy = nose[1] - h / 2
    left_cheek = np.array(landmarks[LEFT_CHEEK])
    right_cheek = np.array(landmarks[RIGHT_CHEEK])
    face_width = np.linalg.norm(left_cheek - right_cheek) + 1e-6
    return dy / face_width, dx / face_width


def head_roll(landmarks):
    """双眼连线相对水平的夹角 roll (弧度), 正值 = 向右歪头。"""
    left = np.mean([landmarks[i] for i in LEFT_EYE_IDX], axis=0)
    right = np.mean([landmarks[i] for i in RIGHT_EYE_IDX], axis=0)
    dx = right[0] - left[0]
    dy = right[1] - left[1]
    return math.atan2(dy, dx)


def head_move_direction(pitch, yaw, yaw_deadzone, pitch_deadzone):
    """将 yaw/pitch 偏差映射到移动方向 (供鼠标/方向键使用)。

    返回 "" 或 move_left / move_right / move_up / move_down。
    """
    if abs(yaw) >= abs(pitch):
        if yaw > yaw_deadzone:
            return "move_right"
        if yaw < -yaw_deadzone:
            return "move_left"
    else:
        if pitch > pitch_deadzone:
            return "move_down"
        if pitch < -pitch_deadzone:
            return "move_up"
    return ""


def extract_features(landmarks, frame_shape) -> Features:
    ear_left = eye_aspect_ratio(landmarks, LEFT_EYE_IDX)
    ear_right = eye_aspect_ratio(landmarks, RIGHT_EYE_IDX)
    ear = (ear_left + ear_right) / 2.0
    mar = mouth_aspect_ratio(landmarks)
    pitch, yaw = head_pose(landmarks, frame_shape)
    roll = head_roll(landmarks)
    return Features(ear, ear_left, ear_right, mar, pitch, yaw, roll)