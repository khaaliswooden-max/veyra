import sys
from pathlib import Path

import pytest

# Add src to python path for tests
src_path = Path(__file__).parent.parent / "src"
sys.path.append(str(src_path))


@pytest.fixture
def sample_config():
    return {"system": {"name": "Veyra Test"}}
