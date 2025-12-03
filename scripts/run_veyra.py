#!/usr/bin/env python
import sys
from pathlib import Path

# Add src to python path
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir / "src"))

from veyra.__main__ import main

if __name__ == "__main__":
    main()
