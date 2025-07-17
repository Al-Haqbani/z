from __future__ import annotations
import time
import random
from typing import List, Dict

from is_scanner.js_scanner import run_smart_scan

class JSFileSearcher:
    """Search archived JavaScript files for leaks."""

    def __init__(self, token: str | None = None, **kwargs):
        pass

    def search(
        self,
        keyword: str,
        *,
        include_subdomains: bool = False,
        use_wayback: bool = True,
        use_linkfinder: bool = False,
        progress_callback=None,
        result_callback=None,
        **kwargs,
    ) -> List[Dict[str, str]]:
        results = []
        found = run_smart_scan(
            keyword,
            include_subdomains=include_subdomains,
            use_wayback=use_wayback,
            use_linkfinder=use_linkfinder,
        )
        for idx, item in enumerate(found, 1):
            res = {
                "source": "JSFile",
                "file": item["url"],
                "leak_type": item["leak_type"],
                "value": item["value"],
            }
            results.append(res)
            if result_callback:
                result_callback(res, idx)
            if progress_callback:
                progress_callback({"leaks": idx, "platform": "jsfile"})
            time.sleep(random.uniform(0.1, 0.3))
        return results
