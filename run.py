"""Start the bot: python run.py"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from discord_ai.main import main

if __name__ == "__main__":
    main()
