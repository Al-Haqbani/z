from .github_api import GitHubSearcher
from .dockerhub_scraper import DockerHubSearcher
from .huggingface_scraper import HuggingFaceSearcher
from .npm_scraper import NPMPackageSearcher
from .pypi_scraper import PyPiPackageSearcher
from .reddit_scraper import RedditSearcher
from .pastebin_scraper import PastebinSearcher
from .gitlab_api import GitLabSearcher
from .swaggerhub_scraper import SwaggerHubSearcher
from .ai_verifier import is_valid_leak


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
    }

    @classmethod
    def _verify_results(cls, results, verify_ai=False):
        if not verify_ai:
            return results
        verified = []
        for item in results:
            if is_valid_leak(item.get("value", "")):
                verified.append(item)
        return verified

    @classmethod
    def start_search(
        cls,
        platform,
        keyword,
        employees=None,
        verify_ai=False,
        tokens=None,
        **kwargs,
    ):
        tokens = tokens or {}
        searcher_cls = cls.PLATFORM_MAP.get(platform)
        if not searcher_cls:
            print(f"Unsupported platform: {platform}")
            return []
        token = tokens.get(platform)
        searcher = searcher_cls(token=token, **kwargs)
        results = searcher.search(keyword, employees=employees, **kwargs)
        return cls._verify_results(results, verify_ai)

    @classmethod
    def run_full_auto_mode(
        cls,
        keyword,
        employees=None,
        verify_ai=False,
        tokens=None,
        **kwargs,
    ):
        results = []
        tokens = tokens or {}
        for name, searcher_cls in cls.PLATFORM_MAP.items():
            token = tokens.get(name)
            searcher = searcher_cls(token=token, **kwargs)
            found = searcher.search(keyword, employees=employees, **kwargs)
            results.extend(found)
        return cls._verify_results(results, verify_ai)
