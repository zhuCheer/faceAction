# TASK — 摸鱼/懒人面部控制助手任务拆解

> 状态: 草案 (Draft)
> 版本: 0.5.0
> 日期: 2026-10-16
> 相关文档: [SPEC.md](./SPEC.md) | [PLAN.md](./PLAN.md) | [IMPLEMENT.md](./IMPLEMENT.md)

---

## 1. 本次目标

聚焦「懒人 / 顽梗 / 摸鱼」核心场景，把产品收敛为两个一级功能，并新增防偷窥。

- **保留**：看抖音（改名自"刷抖音"）。
- **新增**：防偷窥。
- **移除**：鼠标操作、方向键、滚动翻页、媒体控制、确认/取消 五个一级功能及其映射、测试。

---

## 2. 任务清单

| ID | 任务 | 产出 | 状态 |
|----|------|------|------|
| C1 | 调整文档（SPEC/PLAN/TASK/IMPLEMENT/USER_GUIDE/READMD） | 需求一致 | ☑ |
| C2 | 精简 `constants.py`（BEHAVIORS 仅 2 项、MODE_ACTIONS/MODE_HINTS 精简） | 2 项一级菜单 | ☐ |
| C3 | 新增 `core/anti_peep.py`（防偷窥控制器，纯逻辑） | 防偷窥状态机 | ☐ |
| C4 | 改造 `state_machine.py`（防偷窥点头切换、移除鼠标中心等） | 菜单/模式逻辑 | ☐ |
| C5 | 精简 `mapper.py`（仅看抖音映射） | 指令映射 | ☐ |
| C6 | 扩展 `executor.py`（`show_desktop`/`restore_douyin`/浏览器标记） | Win+D/恢复 | ☐ |
| C7 | 改造 `engine.py`（无人脸保留模式、接入防偷窥） | 端到端编排 | ☐ |
| C8 | 更新 `ui/main_window.py`（防偷窥状态展示） | UI 反馈 | ☐ |
| C9 | 更新/新增单元测试（state_machine/mapper/anti_peep） | 通过 | ☐ |
| C10 | 运行 `python -m unittest discover -s tests` 并通过 | 验证 | ☐ |

---

## 3. 验证策略

### 3.1 自动化测试
- `test_anti_peep.py`：验证 `toggle`、`on_face` 边沿输出 `hide`/`restore`、关闭时无输出。
- `test_state_machine.py`：验证菜单 2 项、看抖音进入、防偷窥点头切换、张嘴×2 返回。
- `test_mapper.py`：验证看抖音映射，已移除的映射不影响。

### 3.2 手动验收
- 面对摄像头：左右摇头切换「看抖音/防偷窥」；点头进入看抖音并打开抖音。
- 点头/抬头分别触发 ↓/↑；连续张嘴两次返回。
- 高亮「防偷窥」点头开启；转头/离开画面触发 `Win+D`；回到画面恢复浏览器/打开抖音。
- 在「防偷窥」开启状态下进入看抖音，验证方向键与防偷窥并存。