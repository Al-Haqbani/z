#!/bin/bash
# Launch web interface after installing deps
python3 -m pip install --user -r requirements.txt
python3 emploleaks.py --web "$@"
