"""
Vercel Serverless Entry Point
=============================
This file is the entry point for Vercel's Python runtime.
It imports the Flask app from the backend package.
"""

import sys
import os

# Add the backend directory to the Python path so we can import app
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app import app
