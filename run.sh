#!/bin/bash
# EasyTest Backend - Quick Start Script

cd "$(dirname "$0")"
source ../backend-venv/bin/activate

# Use python3 explicitly (works on macOS)
python3 manage.py "$@"

