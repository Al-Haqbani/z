#!/bin/bash
# Simple setup script for EmploLeaksGuardian
set -e
python3 -m pip install --user -r requirements.txt
echo "Dependencies installed. Run: python3 emploleaks.py"
