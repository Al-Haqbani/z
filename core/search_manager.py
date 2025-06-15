from .github_api import GitHubSearcher
from .dockerhub_scraper import DockerHubSearcher
from .huggingface_scraper import HuggingFaceSearcher
from .npm_scraper import NPMPackageSearcher
from .pypi_scraper import PyPiPackageSearcher
from .reddit_scraper import RedditSearcher
from .pastebin_scraper import PastebinSearcher
from .gitlab_api import GitLabSearcher
from .swaggerhub_scraper import SwaggerHubSearcher
from .gist_searcher import GitHubGistSearcher
from .grayhat_scraper import GrayHatSearcher
from .ai_verifier import is_valid_leak
from .token_verifier import verify_token
from utils.notifications import send_telegram, send_discord


class SearchManager:
    PLATFORM_MAP = {
        "github": GitHubSearcher,
        "dockerhub": DockerHubSearcher,
        "huggingface": HuggingFaceSearcher,
        "npm": NPMPackageSearcher,
        "pypi": PyPiPackageSearcher,
        "reddit": RedditSearcher,
        "pastebin": PastebinSearcher,
        "gitlab": GitLabSearcher,
        "swaggerhub": SwaggerHubSearcher,
        "gist": GitHubGistSearcher,
        "grayhat": GrayHatSearcher,
    }

    @staticmethod
    def _dedup_results(results):
        seen = set()
        out = []
        for item in results:
            key = (item.get("source"), item.get("file"), item.get("value"))
            if key in seen:
                continue
            seen.add(key)
            out.append(item)
        return out

    @staticmethod
    def _send_notifications(results):
        if not results:
            return
        lines = [f"{r['leak_type']} -> {r['file']}" for r in results]
        message = "New leaks found:\n" + "\n".join(lines)
        send_telegram(message)
        send_discord(message)

    @classmethod
    def _verify_results(cls, results, verify_ai=False, active_verify=False):
        filtered = []
        if verify_ai:
            for item in results:
                if is_valid_leak(item.get("value", "")):
                    filtered.append(item)
        else:
            filtered = list(results)

        for item in filtered:
            if active_verify:
                item["active"] = verify_token(
                    item.get("leak_type", ""), item.get("value", "")
                )
            else:
                item["active"] = None

        return cls._dedup_results(filtered)

    @classmethod
    def start_search(
        cls,
        platform,
        keyword,
        employees=None,
        organization=None,
        verify_ai=False,
        active_verify=False,
        notify=False,
        tokens=None,
        full_scan=False,
        scan_wayback=False,
        result_callback=None,
        **kwargs,
    ):
        tokens = tokens or {}
        searcher_cls = cls.PLATFORM_MAP.get(platform)
        if not searcher_cls:
            print(f"Unsupported platform: {platform}")
            return []
        token = tokens.get(platform)
        searcher = searcher_cls(token=token, **kwargs)
        results = searcher.search(
            keyword,
            employees=employees,
            organization=organization,
            full_scan=full_scan,
            scan_wayback=scan_wayback,
            **kwargs,
        )
        results = cls._verify_results(results, verify_ai, active_verify)
        if result_callback:
            for idx, item in enumerate(results, 1):
                result_callback(item, idx)
        if notify:
            cls._send_notifications(results)
        return results

    @classmethod
    def run_full_auto_mode(
        cls,
        keyword,
        employees=None,
        organization=None,
        verify_ai=False,
        active_verify=False,
        notify=False,
        tokens=None,
        full_scan=False,
        scan_wayback=False,
        result_callback=None,
        **kwargs,
    ):
        """Run searches on all platforms concurrently."""
        from concurrent.futures import ThreadPoolExecutor, as_completed

        results = []
        tokens = tokens or {}

        def _worker(name, searcher_cls):
            token = tokens.get(name)
            searcher = searcher_cls(token=token, **kwargs)
            return searcher.search(
                keyword,
                employees=employees,
                organization=organization,
                full_scan=full_scan,
                scan_wayback=scan_wayback,
                **kwargs,
            )

        with ThreadPoolExecutor(max_workers=len(cls.PLATFORM_MAP)) as ex:
            future_map = {
                ex.submit(_worker, name, scls): name
                for name, scls in cls.PLATFORM_MAP.items()
            }
            for fut in as_completed(future_map):
                try:
                    res = fut.result()
                    results.extend(res)
                    verified = cls._verify_results(res, verify_ai, active_verify)
                    if result_callback:
                        for idx, item in enumerate(verified, 1):
                            result_callback(item, idx)
                except Exception as exc:
                    if not kwargs.get("silent", False):
                        print(f"{future_map[fut]} search error: {exc}")

        results = cls._verify_results(results, verify_ai, active_verify)
        if notify:
            cls._send_notifications(results)
        return results
