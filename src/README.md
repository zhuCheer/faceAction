# 摸鱼/懒人面部控制助手

用点头/抬头刷抖音、左右摇头切换菜单；开启「防偷窥」后，人离开画面自动切桌面、人回来自动恢复浏览器/抖音。全程本地离线运行，摄像头画面不上传。

## 快速开始

```powershell
cd src
.\start.ps1              # 默认摄像头 (index 0)
.\start.ps1 -Camera 1    # 指定摄像头
.\start.ps1 -Test        # 运行核心逻辑单元测试（无需摄像头）
```

或手动运行：

```powershell
python app.py            # 需先安装依赖
python app.py 1
python -m unittest discover -s tests -v
```

首次运行 `start.ps1` 会自动创建 `.venv` 并安装依赖（mediapipe 体积较大，需等待）。

> 依赖：Python 3.9+（mediapipe 0.10.14 建议 3.9）。Windows 10/11。

## 目录结构（分层）

```
src/
├── app.py                  # 程序入口：加载配置 → 引擎 → 主窗口
├── start.ps1               # 一键启动 / 测试脚本
├── requirements.txt        # 依赖清单
├── config/
│   └── settings.json       # 资源：首页 / 书签 / 灵敏度 / 摄像头
├── core/                   # 业务与算法逻辑（无 UI 依赖）
│   ├── constants.py        #   关键点索引 + 阈值 + 行为模式定义
│   ├── features.py         #   特征提取（EAR/MAR/位姿）
│   ├── detector.py         #   动作检测（眨眼/张嘴/点头/方向化摇头/歪头）
│   ├── anti_peep.py        #   防偷窥控制器（人脸边沿 → 切桌面/恢复）
│   ├── state_machine.py    #   行为锚定状态机（看抖音/防偷窥）
│   ├── mapper.py           #   动作 → 指令 映射
│   ├── executor.py         #   指令执行（Win32 SendInput / 默认浏览器）
│   ├── tracker.py          #   MediaPipe FaceMesh 封装
│   ├── engine.py           #   流水线编排（跟踪→识别→执行）
│   └── config.py           #   配置加载
├── ui/                     # 界面层（PySide6）
│   ├── theme.py            #   深色主题配色 + QSS
│   └── main_window.py      #   两态窗口 + 摄像头线程 + 悬浮提示
└── tests/                  # 单元测试（core 纯逻辑，无需摄像头）
    ├── test_features.py
    ├── test_detector.py
    ├── test_anti_peep.py
    ├── test_state_machine.py
    ├── test_mapper.py
    └── test_config.py
```

分层原则：`core/` 只做算法与业务逻辑、不依赖 UI 与摄像头硬件本身（可独立单测）；`ui/` 只负责展示与线程调度；`config/` 放可改写的用户资源；`tests/` 覆盖 `core/` 纯逻辑。

## 界面说明

- **选择态（大窗口）**：居中大窗，顶部显示摄像头画面，下方两个一级卡片（看抖音 / 防偷窥），当前项高亮。
- **看抖音态（小窗口）**：点头进入后窗口缩到屏幕右下角，画面占满；点头/抬头切视频，连续张嘴两次返回选择态。
- **防偷窥**：在菜单高亮「防偷窥」时点头切换开/关；开启后脸离开画面自动 `Win+D` 切桌面，脸回来自动恢复浏览器/打开抖音。
- 窗口无边框、置顶、可拖动；点击右上角关闭或直接关进程退出。

## 配色

| 名称 | 色值 |
|------|------|
| 底色 | `#027373` |
| 底色2 | `#193D47` |
| 浅底3 | `#33A39B` |
| 高亮 | `#C2FE06` |
| 白色 | `#FFFFFF` |

字体统一使用「微软雅黑」，QSS 中通过透明度/饱和度延伸出一整套深色视觉。

## 配置

编辑 `config/settings.json`：

```json
{
  "mouse_step": 16,
  "camera_index": 0
}
```

- `mouse_step`：看抖音模式下，头部移动光标的每帧最大像素（灵敏度）。
- `camera_index`：要使用的摄像头索引（默认 0）。

> `homepage` / `bookmarks` 为历史字段，当前「看抖音 + 防偷窥」两功能不再使用。

详细操作说明见 [`_doc/USER_GUIDE.md`](../_doc/USER_GUIDE.md)。