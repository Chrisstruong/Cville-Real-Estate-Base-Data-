"""Compatibility entrypoint for hosts configured with ``uvicorn main:app``.

The application itself lives in ``app.main``.
"""

from app.main import app
