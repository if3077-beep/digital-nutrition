"""让 pytest 能 import digital_nutrition 包。"""
import sys
from pathlib import Path

# 把项目根加到 sys.path，让 `from digital_nutrition import ...` 工作
sys.path.insert(0, str(Path(__file__).parent.resolve()))
