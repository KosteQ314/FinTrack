import os
import sys

# hide the console window on Windows
if sys.platform == "win32":
    import ctypes

    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

import run
