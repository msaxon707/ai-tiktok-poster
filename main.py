"""Backward-compatible entry point that delegates to the CLI."""

from __future__ import annotations

from cli import main


if __name__ == "__main__":
    main()
