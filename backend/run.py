#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Entry point to run the Flask application."""
import os
import sys

# Thiết lập UTF-8 encoding cho stdout/stderr
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')

if __name__ == "__main__":
    from app.main import app

    host = os.getenv("APP_HOST", "0.0.0.0")
    port = int(os.getenv("APP_PORT", "8000"))
    app.run(host=host, port=port, debug=True)
