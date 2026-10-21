"""产品入口：加载配置、初始化识别引擎与主窗口。

用法:
    python app.py                 # 默认摄像头 + 默认配置
    python app.py 1               # 指定摄像头 index
"""
import os
import sys

# 允许 `python app.py` 直接运行, 保证 `core` / `ui` 可导入
_SRC = os.path.dirname(os.path.abspath(__file__))
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from PySide6.QtWidgets import QApplication

from core.config import Config
from core.engine import RecognitionEngine
from ui.main_window import MainWindow
from ui.theme import build_stylesheet, set_theme
from i18n import set_language, t


def main() -> int:
    config = Config.load()
    if len(sys.argv) > 1:
        try:
            config.camera_index = int(sys.argv[1])
        except ValueError:
            pass

    set_language(config.language)

    app = QApplication(sys.argv)
    app.setApplicationName(t("app_name"))
    set_theme(config.theme)
    app.setStyleSheet(build_stylesheet())

    engine = RecognitionEngine(config)
    window = MainWindow(config, engine)
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())