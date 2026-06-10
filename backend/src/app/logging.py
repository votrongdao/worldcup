"""Structured logging configuration (JSON logs -> App Insights)."""
from __future__ import annotations
import logging


def configure() -> None:
    logging.basicConfig(level=logging.INFO)
