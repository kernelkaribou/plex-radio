#!/usr/bin/env python3
"""
WSGI entry point for Plex Radio API
"""
import os
import sys

# Add the server directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Import the Flask app
from plex_radio_api import app

# Optional: Additional production setup
if __name__ != "__main__":
    # This runs when imported by Gunicorn
    print("WSGI: Plex Radio API loaded for production")

if __name__ == "__main__":
    # This runs when executed directly
    app.run(host='0.0.0.0', port=5000, debug=True)