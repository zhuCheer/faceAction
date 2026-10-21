"""人脸跟踪：封装 MediaPipe FaceMesh，输出 468 关键点。"""
import cv2
import mediapipe as mp

from .constants import MAX_NUM_FACES
from .features import extract_features


class FaceTracker:
    def __init__(self):
        self.face_mesh = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=MAX_NUM_FACES,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        # 预取 FaceMesh 轮廓连接集 (只画少量轮廓线，避免网格过密)
        self._contours = list(mp.solutions.face_mesh.FACEMESH_CONTOURS)

    def detect(self, rgb):
        return self.face_mesh.process(rgb)

    def face_count(self, results):
        """检测到的人脸数量 (无人脸返回 0)。"""
        return len(results.multi_face_landmarks) if results.multi_face_landmarks else 0

    def _points(self, lm, frame_shape):
        h, w = frame_shape[:2]
        return [(int(p.x * w), int(p.y * h)) for p in lm.landmark]

    def landmarks(self, results, frame_shape):
        """返回第一张人脸的关键点列表; 无人脸返回 None。"""
        if not results.multi_face_landmarks:
            return None
        return self._points(results.multi_face_landmarks[0], frame_shape)

    def all_landmarks(self, results, frame_shape):
        """返回所有人脸的关键点列表 [[(x, y), ...], ...]; 无人脸返回空列表。"""
        if not results.multi_face_landmarks:
            return []
        return [self._points(lm, frame_shape) for lm in results.multi_face_landmarks]

    def features(self, landmarks, frame_shape):
        return extract_features(landmarks, frame_shape)

    def draw_mesh(self, bgr, landmarks, color=(6, 254, 194), thickness=2):
        """在 bgr 帧上叠加 FaceMesh 轮廓线条 (原地绘制并返回该帧)。"""
        if not landmarks:
            return bgr
        for a, b in self._contours:
            cv2.line(bgr, landmarks[a], landmarks[b], color, thickness)
        return bgr

    def draw_face_box(self, bgr, landmarks, color=(6, 254, 194), thickness=2, pad=6):
        """在 bgr 帧上叠加人脸区域外接框 (无人脸时返回原帧)。"""
        if not landmarks:
            return bgr
        h, w = bgr.shape[:2]
        xs = [p[0] for p in landmarks]
        ys = [p[1] for p in landmarks]
        x1 = max(0, min(xs) - pad)
        y1 = max(0, min(ys) - pad)
        x2 = min(w, max(xs) + pad)
        y2 = min(h, max(ys) + pad)
        cv2.rectangle(bgr, (x1, y1), (x2, y2), color, thickness)
        return bgr

    def draw_face_boxes(self, bgr, faces, color=(6, 254, 194), thickness=2, pad=6):
        """给每张人脸叠加外接框 (原地绘制并返回该帧)。"""
        for landmarks in faces:
            self.draw_face_box(bgr, landmarks, color, thickness, pad)
        return bgr

    def close(self):
        self.face_mesh.close()