import sys
import argparse
from veyra.core import VeyraCore
from veyra.logging_utils import setup_logging

def main() -> None:
    parser = argparse.ArgumentParser(description="Veyra: Temporal Reconstruction System")
    parser.add_argument("--config", type=str, default="configs/default.yaml", help="Path to configuration file")
    args = parser.parse_args()

    setup_logging()
    
    core = VeyraCore()
    core.run()

if __name__ == "__main__":
    main()
