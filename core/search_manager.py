from .github_api import GitHubSearcher
from .dockerhub_scraper import DockerHubSearcher
from .huggingface_scraper import HuggingFaceSearcher
from .npm_scraper import NPMPackageSearcher
from .pypi_scraper import PyPiPackageSearcher
from .reddit_scraper import RedditSearcher
from .pastebin_scraper import PastebinSearcher


class SearchManager:
    PLATFORM_MAP = {
        "github": GitHubSearcher,
        "dockerhub": DockerHubSearcher,
        "huggingface": HuggingFaceSearcher,
        "npm": NPMPackageSearcher,
        "pypi": PyPiPackageSearcher,
        "reddit": RedditSearcher,
        "pastebin": PastebinSearcher,
    }

    @classmethod
    def start_search(cls, platform, keyword, employees=None, **kwargs):
        searcher_cls = cls.PLATFORM_MAP.get(platform)
        if not searcher_cls:
            print(f"Unsupported platform: {platform}")
            return []
        searcher = searcher_cls(**kwargs)
        return searcher.search(keyword, employees=employees, **kwargs)

    @classmethod
    def run_full_auto_mode(cls, keyword, employees=None, **kwargs):
        results = []
        for name, searcher_cls in cls.PLATFORM_MAP.items():
            searcher = searcher_cls(**kwargs)
            results.extend(searcher.search(keyword, employees=employees, **kwargs))
        return results
