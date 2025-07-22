import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location("emploleaks_cli", Path(__file__).resolve().parent.parent / 'emploleaks.py')
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)
main = _module.main
