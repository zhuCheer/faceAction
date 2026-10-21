# IMPLEMENT — 摸鱼/懒人面部控制助手实现规范

> 状态: 草案 (Draft)
> 版本: 0.5.0
> 日期: 2026-10-16
> 相关文档: [SPEC.md](./SPEC.md) | [PLAN.md](./PLAN.md) | [TASK.md](./TASK.md)

---

## 1. 目的

统一代码实现规范，并作为**实现记录（Change Log）**承载任务完成要点，供后续维护与追溯。

---

## 2. 编码规范

- Python 3.10+，类型注解。
- 遵循 PEP 8；模块与类职责单一；纯逻辑可单测。
- 事件/数据模型使用 `@dataclass`。
- 关键算法（nod/shake/防偷窥边沿）写清判定依据。
- 摄像头/模型初始化失败需有用户可读提示，不允许静默崩溃。

---

## 3. 核心契约

### 3.1 AntiPeep（新增）
```python
class AntiPeep:
    def __init__(self):          # enabled=False, face_present=True
    def toggle(self) -> None     # 开/关切换
    def on_face(self, present: bool) -> list[str]  # -> ["hide"] / ["restore"] / []
```

### 3.2 StateMachine 与 Step
```python
@dataclass
class Step:
    mode: str          # None=选择态, "douyin"
    menu_index: int
    gestures: list     # [(name, payload), ...]
    hint: str
    bubble: str
    continuous: str
    anti_peep: bool    # 防偷窥是否开启（供 UI 展示）

class BehaviorStateMachine:
    def __init__(self, anti_peep: AntiPeep = None)
    def update(self, events, head_dir, now) -> Step
```

### 3.3 Executor（新增方法）
```python
def show_desktop(self) -> None       # Win+D
def restore_douyin(self, url) -> None  # 已开浏览器→Win+D；否则 open_url
def open_url(self, url) -> None      # 标记 browser_opened=True
```

### 3.4 线程约束
- 沿用单线程 CameraThread；禁止在识别线程直接操作 UI（统一经 Qt 信号返回 `step`）。

---

## 4. 实现记录（Change Log）

### [2026-10-16] C1-C10 — 摸鱼/懒人版本重构
- 状态: 完成
- 实现要点:
  - `BEHAVIORS` 收敛为 `看抖音 / 防偷窥`；移除五个通用一级功能及映射、测试。
  - 新增 `core/anti_peep.py`，用「人脸边沿」驱动 hide/restore。
  - `state_machine` 高亮防偷窥时点头调用 `toggle()`，不进入模式。
  - 引擎无人脸时保留 `sm.mode`，使看抖音态跨越人脸丢失。
  - `executor` 新增 `show_desktop` / `restore_douyin`，用 `Win+D` 实现切换与恢复。
- 遇到的问题与决策:
  - `Win+D` 是切换型快捷键，采用人脸边沿对称触发，避免手动操作导致失步。
  - 打开浏览器无窗口句柄，用 `Win+D` 二次切换实现"恢复"，符合需求"恢复原状"。
- 待办/遗留:
  - 更精确的浏览器窗口恢复（如按进程名捕获句柄）作为可选增强。