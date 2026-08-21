"""Cấu hình pytest cho backend - đặt biến môi trường mặc định trước khi import app."""

import os

os.environ.setdefault("RECOGNITION_PROVIDER", "mock")
os.environ.setdefault("COPILOT_PROVIDER", "rule_based")