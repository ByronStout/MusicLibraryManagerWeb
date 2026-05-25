# Ensures the project root is on sys.path so `from app import app` works
# regardless of where pytest is invoked from.
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
