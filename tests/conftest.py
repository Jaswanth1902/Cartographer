import sys
from pathlib import Path

# Add project root to sys.path
cartographer_root = Path(__file__).resolve().parent.parent
if str(cartographer_root) not in sys.path:
    sys.path.insert(0, str(cartographer_root))
