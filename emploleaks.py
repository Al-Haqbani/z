import sys
from core.token_manager import get_github_token
from core.search_manager import SearchManager
from core.github_api import GitHubSearcher
from output.terminal_output import print_results

try:
    from webapp import app as web_app
except Exception:
    web_app = None


def main():
    print("EmploLeaksGuardian - Simple Leak Scanner")
    token = get_github_token()
    while True:
        print("\nOptions:\n1. Normal Scan\n2. Full Auto Mode\n3. Smart JS Scan\n4. Web Interface\n5. Exit")
        choice = input("Select option: ")
        if choice == "1":
            platform = input("Platform (github/dockerhub/huggingface/npm/pypi/reddit/pastebin): ")
            keyword = input("Keyword: ")
            use_emp = input("Search employee accounts? (y/N): ").lower() == "y"
            employees = None
            if use_emp:
                repo = input("GitHub repository (owner/repo) for lookup: ")
                employees = GitHubSearcher.get_repo_contributors(repo, token)
            verify_ai = input("Verify leaks with AI? (y/N): ").lower() == "y"
            results = SearchManager.start_search(
                platform, keyword, token=token, employees=employees, verify_ai=verify_ai
            )
            if results:
                print_results(results)
            else:
                print("No leaks found.")
        elif choice == "2":
            keyword = input("Keyword: ")
            use_emp = input("Search employee accounts? (y/N): ").lower() == "y"
            employees = None
            if use_emp:
                repo = input("GitHub repository (owner/repo) for lookup: ")
                employees = GitHubSearcher.get_repo_contributors(repo, token)
            verify_ai = input("Verify leaks with AI? (y/N): ").lower() == "y"
            results = SearchManager.run_full_auto_mode(
                keyword, token=token, employees=employees, verify_ai=verify_ai
            )
            if results:
                print_results(results)
            else:
                print("No leaks found.")
        elif choice == "3":
            from is_scanner.js_scanner import run_smart_scan

            domain = input("Domain: ")
            sub = input("Enumerate subdomains? (y/N): ").lower() == "y"
            use_wb = input("Use Wayback? (Y/n): ").lower() != "n"
            use_lf = input("Run LinkFinder? (y/N): ").lower() == "y"
            found = run_smart_scan(domain, include_subdomains=sub, use_wayback=use_wb, use_linkfinder=use_lf)
            results = [
                {
                    "source": "JavaScript",
                    "file": item["url"],
                    "leak_type": item["leak_type"],
                    "value": item["value"],
                }
                for item in found
            ]
            if results:
                print_results(results)
            else:
                print("No leaks found.")
        elif choice == "4":
            if web_app:
                web_app.run(port=8000)
            else:
                print("Web interface not available (Flask missing)")
        elif choice == "5":
            sys.exit()
        else:
            print("Invalid option")


if __name__ == "__main__":
    main()
