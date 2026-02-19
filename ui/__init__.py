"""
UI модуль для AHK Manipulator
"""

__all__ = ["MainWindow"]


def __getattr__(name):
    if name == "MainWindow":
        from ui.main_window import MainWindow
        return MainWindow
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
