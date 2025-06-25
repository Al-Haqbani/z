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
from .bitbucket_scraper import BitbucketSearcher
from .grayhat_scraper import GrayHatSearcher
from .gitea_api import GiteaSearcher
from .recon_searcher import ReconSearcher
from .trufflehog_searcher import TruffleHogSearcher
from .ai_verifier import is_valid_leak
from .leak_verifier import verify_leak
from utils.logger import logger
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
        "bitbucket": BitbucketSearcher,
        "swaggerhub": SwaggerHubSearcher,
        "gist": GitHubGistSearcher,
        "grayhat": GrayHatSearcher,
        "gitea": GiteaSearcher,
        "recon": ReconSearcher,
        "trufflehog": TruffleHogSearcher,
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

        filtered = cls._dedup_results(filtered)

        if active_verify and filtered:
            from concurrent.futures import ThreadPoolExecutor, as_completed

            def worker(item):
                try:
                    return verify_leak(item.get("leak_type", ""), item.get("value", ""))
                except Exception as exc:
                    logger.warning("Verification error for %s: %s", item.get("value"), exc)
                    return False

            with ThreadPoolExecutor(max_workers=8) as ex:
                future_map = {ex.submit(worker, it): it for it in filtered}
                for fut in as_completed(future_map):
                    item = future_map[fut]
                    try:
                        item["active"] = fut.result()
                    except Exception as exc:
                        item["active"] = False
                        logger.warning("Verification error for %s: %s", item.get("value"), exc)

            # keep only verified results
            filtered = [it for it in filtered if it.get("active")]
        else:
            for item in filtered:
                item["active"] = None

        return filtered

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
        progress_callback=None,
        **kwargs,
    ):
        tokens = tokens or {}
        logger.info("Starting search on %s for '%s'", platform, keyword)
        searcher_cls = cls.PLATFORM_MAP.get(platform)
        if not searcher_cls:
            print(f"Unsupported platform: {platform}")
            return []
        token = tokens.get(platform)
        searcher = searcher_cls(token=token, **kwargs)

        def wrapped_cb(item, idx):
            if active_verify:
                try:
                    item["active"] = verify_leak(
                        item.get("leak_type", ""), item.get("value", "")
                    )
                    if not item["active"]:
                        return
                except Exception as exc:  # pragma: no cover - best effort
                    item["active"] = False
            if result_callback:
                result_callback(item, idx)

        cb = wrapped_cb if result_callback else None
        results = searcher.search(
            keyword,
            employees=employees,
            organization=organization,
            full_scan=full_scan,
            scan_wayback=scan_wayback,
            progress_callback=progress_callback,
            result_callback=cb,
            **kwargs,
        )
        results = cls._verify_results(results, verify_ai, active_verify)
        if notify:
            cls._send_notifications(results)
        logger.info("Finished search on %s with %d results", platform, len(results))
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
        progress_callback=None,
        **kwargs,
    ):
        """Run searches on all platforms concurrently."""
        from concurrent.futures import ThreadPoolExecutor, as_completed
        logger.info("Starting full auto mode for '%s'", keyword)
        results = []
        tokens = tokens or {}

        def _worker(name, searcher_cls):
            token = tokens.get(name)
            searcher = searcher_cls(token=token, **kwargs)

            def wrapped_cb(item, idx):
                if active_verify:
                    try:
                        item["active"] = verify_leak(
                            item.get("leak_type", ""), item.get("value", "")
                        )
                        if not item["active"]:
                            return
                    except Exception:
                        item["active"] = False
                if result_callback:
                    result_callback(item, idx)

            cb = wrapped_cb if result_callback else None
            return searcher.search(
                keyword,
                employees=employees,
                organization=organization,
                full_scan=full_scan,
                scan_wayback=scan_wayback,
                progress_callback=progress_callback,
                result_callback=cb,
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
                except Exception as exc:
                    if not kwargs.get("silent", False):
                        print(f"{future_map[fut]} search error: {exc}")

        results = cls._verify_results(results, verify_ai, active_verify)
        if notify:
            cls._send_notifications(results)
        logger.info("Full auto mode finished with %d results", len(results))
        return results
