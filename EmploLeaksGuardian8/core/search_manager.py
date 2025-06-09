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
    def start_search(cls, platform, keyword, **kwargs):
        searcher_cls = cls.PLATFORM_MAP.get(platform)
        if not searcher_cls:
            print(f"Unsupported platform: {platform}")
            return []
        searcher = searcher_cls(**kwargs)
        return searcher.search(keyword, **kwargs)

    @classmethod
    def run_full_auto_mode(cls, keyword, **kwargs):
        results = []
        for name, searcher_cls in cls.PLATFORM_MAP.items():
            searcher = searcher_cls(**kwargs)
            results.extend(searcher.search(keyword, **kwargs))
        return results

    @classmethod
    def github_employee_scan(cls, usernames, keyword, **kwargs):
        """Run GitHub search across repositories of given users."""
        searcher = GitHubSearcher(**kwargs)
        return searcher.search(keyword, usernames=usernames, **kwargs)
