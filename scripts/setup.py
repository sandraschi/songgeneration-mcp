"""Development setup script."""

import subprocess
import sys


def main():
    """Run development setup."""
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-e", ".[dev]"])
    print("✅ Development environment setup complete!")


if __name__ == "__main__":
    main()
