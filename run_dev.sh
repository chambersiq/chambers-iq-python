#!/bin/bash
# Development server with proper reload configuration

# Exclude .git, .venv, and other unnecessary directories from file watching
uvicorn app.main:app \
  --reload \
  --reload-dir app \
  --reload-exclude ".git/*" \
  --reload-exclude ".venv/*" \
  --reload-exclude "__pycache__/*" \
  --host 0.0.0.0 \
  --port 8000
