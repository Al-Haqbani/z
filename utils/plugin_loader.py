import re
import importlib.util
import yaml
from pathlib import Path
from types import ModuleType
from typing import List


class BasePlugin:
    """Base class for search plugins."""

    name = "base"

    def search(self, keyword: str, **kwargs) -> List[dict]:
        raise NotImplementedError


class RegexPlugin(BasePlugin):
    def __init__(self, name: str, patterns: List[str]):
        self.name = name
        self.patterns = [re.compile(p, re.IGNORECASE) for p in patterns]

    def search(self, keyword: str, **kwargs) -> List[dict]:
        # This plugin simply matches patterns against the keyword
        matches = []
        for pat in self.patterns:
            if pat.search(keyword):
                matches.append({"source": self.name, "file": "keyword", "leak_type": self.name, "value": keyword})
        return matches


def load_python_plugin(path: Path) -> BasePlugin:
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore
    for attr in dir(module):
        obj = getattr(module, attr)
        if isinstance(obj, type) and issubclass(obj, BasePlugin) and obj is not BasePlugin:
            return obj()
    return None


def load_yaml_plugin(path: Path) -> BasePlugin:
    data = yaml.safe_load(path.read_text())
    name = data.get("name", path.stem)
    patterns = data.get("patterns", [])
    if not isinstance(patterns, list):
        patterns = [patterns]
    return RegexPlugin(name, patterns)


def load_plugins(paths: List[str]) -> List[BasePlugin]:
    plugins = []
    for p in paths:
        path = Path(p)
        if not path.exists():
            continue
        if path.is_dir():
            for file in path.iterdir():
                if file.suffix == ".py":
                    plugin = load_python_plugin(file)
                    if plugin:
                        plugins.append(plugin)
                elif file.suffix in {".yml", ".yaml"}:
                    plugins.append(load_yaml_plugin(file))
        else:
            if path.suffix == ".py":
                plugin = load_python_plugin(path)
                if plugin:
                    plugins.append(plugin)
            elif path.suffix in {".yml", ".yaml"}:
                plugins.append(load_yaml_plugin(path))
    return plugins

