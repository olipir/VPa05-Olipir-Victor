import subprocess
import sys
import os

script = os.path.join(os.path.dirname(__file__), "main.py")
subprocess.Popen([sys.executable, script], creationflags=subprocess.CREATE_NEW_CONSOLE)
