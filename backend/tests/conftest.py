"""Cấu hình pytest cho backend - đặt biến môi trường mặc định trước khi import app."""

import os

os.environ.setdefault("RECOGNITION_PROVIDER", "mock")
os.environ.setdefault("COPILOT_PROVIDER", "rule_based")
# Cô lập test khỏi .env thật trên máy dev (tránh gọi mạng ngoài khi test).
os.environ.setdefault("OLLAMA_URL", "http://127.0.0.1:1")
os.environ.setdefault("PIX2TEXT_URL", "http://127.0.0.1:1")
os.environ.setdefault("KNOWLEDGE_EXTERNAL_ENABLED", "false")
os.environ.setdefault("KNOWLEDGE_OLLAMA_TRANSLATION_ENABLED", "false")