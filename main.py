from __future__ import annotations

import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
STREAMLIT_APP = PROJECT_ROOT / "app" / "streamlit_app.py"


def main() -> None:
    if not STREAMLIT_APP.exists():
        raise FileNotFoundError(f"Streamlit app not found: {STREAMLIT_APP}")

    command = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(STREAMLIT_APP),
    ]
    subprocess.run(command, check=True)


if __name__ == "__main__":
    main()
