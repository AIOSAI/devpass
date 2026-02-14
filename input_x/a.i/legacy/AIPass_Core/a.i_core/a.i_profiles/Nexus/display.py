import os
import platform

# --- Terminal colors ---
BLUE = '\033[96m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
MAGENTA = '\033[95m'
CYAN = '\033[96m'
RED = '\033[31m'
WHITE = '\033[97m'
RESET = '\033[0m'
BOLD = '\033[1m'

# Enable Windows console
if platform.system() == 'Windows':
    os.system('')

