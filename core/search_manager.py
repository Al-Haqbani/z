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
from .jsfile_searcher import JSFileSearcher
from .trufflehog_searcher import TruffleHogSearcher
from .shorturl_searcher import ShortURLSearcher
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
        "jsfile": JSFileSearcher,
        "trufflehog": TruffleHogSearcher,
        "shorturl": ShortURLSearcher,
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
                    return (False, "")

            with ThreadPoolExecutor(max_workers=8) as ex:
                future_map = {ex.submit(worker, it): it for it in filtered}
                for fut in as_completed(future_map):
                    item = future_map[fut]
                    try:
                        active, poc = fut.result()
                        item["active"] = active
                        item["poc"] = poc
                    except Exception as exc:
                        item["active"] = False
                        item["poc"] = ""
                        logger.warning("Verification error for %s: %s", item.get("value"), exc)

            # keep only verified results
            filtered = [it for it in filtered if it.get("active")]
        else:
            for item in filtered:
                item["active"] = None
                item["poc"] = ""

        # compute risk scores
        from utils.risk_scoring import compute_risk
        counts = {}
        for item in filtered:
            val = item.get("value")
            counts[val] = counts.get(val, 0) + 1
        for item in filtered:
            item["risk"] = compute_risk(item, counts.get(item.get("value"), 1))

        return filtered

    @classmethod
    def start_search(
        cls,
        platform,
        keyword,
        company=None,
        domains=None,
        employees=None,
        organization=None,
        employees_only=False,
        verify_ai=False,
        active_verify=False,
        notify=False,
        tokens=None,
        full_scan=False,
        scan_wayback=False,
        scan_wiki=False,
        scan_releases=False,
        scan_actions=False,
        scan_gists=False,
        follow_docker=False,
        result_callback=None,
        progress_callback=None,
        patterns=None,
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

        leak_count = 0

        def wrapped_cb(item, idx):
            nonlocal leak_count
            if active_verify:
                try:
                    active, poc = verify_leak(
                        item.get("leak_type", ""), item.get("value", "")
                    )
                    item["active"] = active
                    item["poc"] = poc
                    if not active:
                        return
                except Exception as exc:  # pragma: no cover - best effort
                    item["active"] = False
                    item["poc"] = ""
            leak_count += 1
            if result_callback:
                result_callback(item, leak_count)
            if progress_callback:
                wrap_progress({"leaks": leak_count})

        def wrap_progress(ev):
            if progress_callback:
                ev.setdefault("platform", platform)
                progress_callback(ev)

        cb = wrapped_cb if result_callback else None
        try:
            results = searcher.search(
                keyword,
                company=company,
                domains=domains,
                employees=employees,
                organization=organization,
                employees_only=employees_only,
                patterns=patterns,
                full_scan=full_scan,
                scan_wayback=scan_wayback,
                scan_wiki=scan_wiki,
                scan_actions=scan_actions,
                scan_gists=scan_gists,
                progress_callback=wrap_progress,
                result_callback=cb,
                scan_releases=scan_releases,
                **kwargs,
            )
        except Exception as exc:
            logger.error("%s search failed: %s", platform, exc)
            results = []
        results = cls._verify_results(results, verify_ai, active_verify)

        if follow_docker and hasattr(searcher, "docker_images") and searcher.docker_images:
            docker_searcher = DockerHubSearcher()
            for img in searcher.docker_images:
                results.extend(
                    docker_searcher.search(
                        img,
                        result_callback=result_callback,
                        progress_callback=progress_callback,
                    )
                )
        if notify:
            cls._send_notifications(results)
        logger.info("Finished search on %s with %d results", platform, len(results))
        return results

    @classmethod
    def run_full_auto_mode(
       cls,
       keyword,
        company=None,
        domains=None,
        employees=None,
        organization=None,
        employees_only=False,
        verify_ai=False,
        active_verify=False,
        notify=False,
        tokens=None,
        full_scan=False,
        scan_wayback=False,
        scan_wiki=False,
        scan_releases=False,
        scan_actions=False,
        scan_gists=False,
        include_docker=True,
        platforms=None,
        max_threads=None,
        result_callback=None,
        progress_callback=None,
        patterns=None,
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
            leak_count = 0

            def wrapped_cb(item, idx):
                nonlocal leak_count
                if active_verify:
                    try:
                        active, poc = verify_leak(
                            item.get("leak_type", ""), item.get("value", "")
                        )
                        item["active"] = active
                        item["poc"] = poc
                        if not active:
                            return
                    except Exception:
                        item["active"] = False
                        item["poc"] = ""
                leak_count += 1
                if result_callback:
                    result_callback(item, leak_count)
                if progress_callback:
                    wrap_progress({"leaks": leak_count})

            def wrap_progress(ev):
                if progress_callback:
                    ev.setdefault("platform", name)
                    progress_callback(ev)

            cb = wrapped_cb if result_callback else None
            try:
                return searcher.search(
                    keyword,
                    company=company,
                    domains=domains,
                    employees=employees,
                    organization=organization,
                    employees_only=employees_only,
                    patterns=patterns,
                    full_scan=full_scan,
                    scan_wayback=scan_wayback,
                    scan_wiki=scan_wiki,
                    scan_actions=scan_actions,
                    scan_gists=scan_gists,
                    progress_callback=wrap_progress,
                    result_callback=cb,
                    scan_releases=scan_releases,
                    **kwargs,
                )
            except Exception as exc:
                logger.error("%s search failed: %s", name, exc)
                return []

        platform_items = list(cls.PLATFORM_MAP.items())
        if platforms:
            wanted = set(platforms)
            platform_items = [p for p in platform_items if p[0] in wanted]
        if not include_docker:
            platform_items = [p for p in platform_items if p[0] != "dockerhub"]

        max_workers = max_threads or len(platform_items)
        if max_workers < 1:
            max_workers = len(platform_items)
        with ThreadPoolExecutor(max_workers=max_workers) as ex:
            future_map = {
                ex.submit(_worker, name, scls): name
                for name, scls in platform_items
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
