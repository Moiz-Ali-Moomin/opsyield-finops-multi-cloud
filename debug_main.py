#!/usr/bin/env python3
import sys
import os

# Add the current directory to sys.path to allow running without installation
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from opsyield.cli.main import cli

if __name__ == "__main__":
    print(f"Debug mode: Running from {os.path.abspath(os.path.dirname(__file__))}")
    sys.exit(cli())
