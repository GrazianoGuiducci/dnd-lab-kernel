"""Local entry: Python 3.11+, no installation or network access required."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent / 'src'))
from lab_kernel.cli import main
if __name__ == '__main__':
    raise SystemExit(main())
