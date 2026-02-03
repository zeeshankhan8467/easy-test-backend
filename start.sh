#!/bin/bash
cd "$(dirname "$0")"
source ../backend-venv/bin/activate
python3 manage.py runserver
