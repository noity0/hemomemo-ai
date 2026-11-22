# -*- coding: utf-8 -*-
"""Test the mc_bot.py Tuple fix."""
import sys
sys.path.insert(0, r"D:\DigitalBrain")

from agent.mc_bot import duo_play
from typing import Tuple

print("Tuple import test: OK")

# Test duo_play function signature
try:
    # This won't actually connect, but will check the function signature
    duo_play(lambda x: "test", "localhost", names=("TestBot", "TestBot2"))
except Exception as e:
    if "tuple" in str(e).lower() or "tuple" in str(e):
        print("FAIL: Tuple error still present")
    else:
        print("PASS: Function signature OK (connection error expected)")