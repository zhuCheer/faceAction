# PLAN — 摸鱼/懒人面部控制助手技术方案

> 状态: 草案 (Draft)
> 版本: 0.5.0
> 日期: 2026-10-16
> 相关文档: [SPEC.md](./SPEC.md) | [TASK.md](./TASK.md) | [IMPLEMENT.md](./IMPLEMENT.md)

---

## 1. 技术选型

| 模块 | 方案 | 选型理由 |
|------|------|----------|
| 语言/运行时 | Python 3.10+ | 生态成熟、开发快、便于 AI 模型集成 |
| 人脸关键点 | MediaPipe FaceMesh | 468 点实时检测，CPU 可跑，本地离线 |
| 摄像头采集 | OpenCV (`cv2.VideoCapture`) | 跨平台稳定 |
| 图像处理 | OpenCV / NumPy | 计算 EAR/MAR/位姿 |
| 系统指令 | ctypes `SendInput` + `webbrowser` | 零第三方输入依赖；可发送 `Win+D` 与方向键 |
| GUI/预览 | PySide6 (Qt) | 桌面 UI、置顶悬浮窗 |
| 配置 | JSON (标准库) | 无需额外依赖 |
| 测试 | `unittest`（pytest 兼容发现） | 纯逻辑可单测 |

---

## 2. 总体架构

沿用分层架构：

```text
┌─────────────────────────────────────────────┐
│  UI 层 (PySide6)                             │
│  两态窗口 / 单行轮播菜单 / 悬浮提示           │
└───────────────▲──────────────────────────────┘
                │ step / 状态
┌───────────────┴──────────────────────────────┐
│  应用层 (RecognitionEngine)                   │
│  编排：跟踪→特征→动作→状态机→防偷窥→执行      │
└───────────────▲──────────────────────────────┘
                │ 识别结果
┌───────────────┴──────────────────────────────┐
│  识别引擎 (tracker + features + detector)     │
└───────────────▲──────────────────────────────┘
                │ 原始帧
┌───────────────┴──────────────────────────────┐
│  采集层 (CameraSource / CameraThread)         │
└──────────────────────────────────────────────┘

┌──────────────────────────────────────────────┐
│  输出层 (Executor + AntiPeep)                 │
│  方向键 / 打开浏览器 / Win+D                  │
└──────────────────────────────────────────────┘
```

新增 **AntiPeep（防偷窥控制器）**：纯逻辑模块，维护 `enabled` 与人脸 `present` 的边沿，输出 `hide` / `restore` 两个语义命令，由引擎映射到执行器。

---

## 3. 模块设计

### 3.1 BehaviorStateMachine（行为状态机）
- 选择态：`menu_index` 在 `BEHAVIORS = [(douyin, 看抖音), (anti_peep, 防偷窥)]` 间左右摇头切换。
- 点头确认：
  - 高亮「看抖音」→ 进入看抖音模式，产出 `open_douyin`。
  - 高亮「防偷窥」→ 调用 `AntiPeep.toggle()`，**不进入模式**，菜单保持。
- 看抖音态：`nod`/`nod_up`/`double_blink` 按 `MODE_ACTIONS` 解释；连续张嘴×2 返回选择态。

### 3.2 AntiPeep（防偷窥控制器，新增）
```python
class AntiPeep:
    enabled: bool              # 是否开启
    face_present: bool         # 稳定(已确认)的人脸状态
    debounce_seconds: float    # 防抖时长 (默认 0.5s)

    def toggle(self) -> None
    def on_face(self, present: bool, now: float) -> list[str]  # ["hide"] / ["restore"] / []
```

边沿逻辑（带 **500ms 防抖**，抑制来回闪动）：
- `present: True → False` 且持续满 500ms，输出 `hide`（切桌面）。
- `present: False → True` 且持续满 500ms，输出 `restore`（恢复浏览器/打开抖音）。
- 未满防抖时长即变回原状态，不输出任何命令。

### 3.3 Executor（执行器，扩展）
新增：
- `show_desktop()`：发送 `Win+D`（`LWIN` down + `D` down/up + `LWIN` up）。
- `restore_douyin(url)`：若已打开浏览器 → `show_desktop()`（恢复）；否则 `open_url(url)`。
- `open_url(url)`：`webbrowser.open` 并标记 `browser_opened = True`。

### 3.4 RecognitionEngine（引擎，调整）
- 无人脸时 `reset()` 检测器、释放持续按键，但**保留 `sm.mode`**（看抖音态跨越人脸丢失）。
- 每帧先执行防偷窥边沿检测，再走识别/状态机/执行流程。

---

## 4. 数据流与线程模型

```text
CameraThread(采集+识别+执行, 单线程以简化) 
  帧 → FaceTracker.detect → landmarks? 
       ├─ 无 → AntiPeep.on_face(False) → 可能 Win+D
       └─ 有 → 特征 → detector → state_machine → mapper/executor
             → AntiPeep.on_face(True) → 可能恢复
```

> 沿用现有单线程 CameraThread 方案：摄像头读帧、识别、执行在同一线程顺序完成，避免跨线程队列复杂度，满足刷抖音场景的实时性。

---

## 5. 目录结构（现状）

```text
src/
├── app.py
├── start.ps1
├── requirements.txt
├── config/settings.json
├── core/
│   ├── constants.py        # 关键点索引 + 阈值 + BEHAVIORS(2 项)
│   ├── features.py
│   ├── detector.py
│   ├── anti_peep.py        # 新增：防偷窥控制器
│   ├── state_machine.py    # 行为状态机
│   ├── mapper.py           # 看抖音动作→指令
│   ├── executor.py         # SendInput + 浏览器 + Win+D
│   ├── tracker.py
│   └── engine.py
├── ui/
│   ├── theme.py
│   └── main_window.py
└── tests/
    ├── test_features.py
    ├── test_detector.py
    ├── test_anti_peep.py   # 新增
    ├── test_state_machine.py
    ├── test_mapper.py
    └── test_config.py
```

---

## 6. 技术风险与对策

| 风险 | 对策 |
|------|------|
| `Win+D` 是切换快捷键，状态可能因用户手动操作而失步 | 由 `AntiPeep` 以人脸边沿统一驱动 hide/restore，语义简单可控 |
| 无人脸时误触（人脸短暂丢失） | 保留 MediaPipe 连续跟踪；防偷窥带 500ms 防抖，仅在稳定边沿触发，不逐帧重复 |
| 打开浏览器无法获取窗口句柄 | 用 `Win+D` 恢复代替精确窗口控制，符合"恢复到原状"的诉求 |
| 目录/窗口权限被安全软件拦截 | 使用 `SendInput`，文档说明