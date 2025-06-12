import sys
from core.token_manager import get_token, get_github_token
from core.search_manager import SearchManager
from core.github_api import GitHubSearcher
from output.terminal_output import print_results
from report_generator.generate_report import generate_html_report

try:
    from webapp import app as web_app
except Exception:
    web_app = None


def main():
    print("EmploLeaksGuardian - Simple Leak Scanner")
    github_token = get_token("GitHub", "GITHUB_TOKEN")
    gitlab_token = get_token("GitLab", "GITLAB_TOKEN")
    swagger_token = get_token("SwaggerHub", "SWAGGER_TOKEN")
    tokens = {
        "github": github_token,
        "gitlab": gitlab_token,
        "swaggerhub": swagger_token,
    }
    while True:
        print("\nOptions:\n1. Normal Scan\n2. Full Auto Mode\n3. Smart JS Scan\n4. Web Interface\n5. Exit")
        choice = input("Select option: ")
        if choice == "1":
            platform = input("Platform (github/gitlab/swaggerhub/dockerhub/huggingface/npm/pypi/reddit/pastebin): ")
            keyword = input("Keyword: ")
            use_emp = input("Search employee accounts? (y/N): ").lower() == "y"
            employees = None
            if use_emp:
                repo = input("GitHub repository (owner/repo) for lookup: ")
                employees = GitHubSearcher.get_repo_contributors(repo, github_token)
            org = None
            if input("Scan entire GitHub org? (y/N): ").lower() == "y":
                org = input("Organization name: ")
            deep_scan = input("Deep GitHub scan? (y/N): ").lower() == "y"
            verify_ai = input("Verify leaks with AI? (y/N): ").lower() == "y"
            active_verify = input("Active token verify? (y/N): ").lower() == "y"
            notify = input("Send Telegram/Discord alerts? (y/N): ").lower() == "y"
            results = SearchManager.start_search(
                platform,
                keyword,
                employees=employees,
                verify_ai=verify_ai,
                active_verify=active_verify,
                notify=notify,
                tokens=tokens,
                organization=org,
                deep_scan=deep_scan,
            )
            if results:
                print_results(results)
                report_path = generate_html_report(results, path="results.html")
                print(f"Report saved to {report_path}")
            else:
                print("No leaks found.")
        elif choice == "2":
            keyword = input("Keyword: ")
            use_emp = input("Search employee accounts? (y/N): ").lower() == "y"
            employees = None
            if use_emp:
                repo = input("GitHub repository (owner/repo) for lookup: ")
                employees = GitHubSearcher.get_repo_contributors(repo, github_token)
            org = None
            if input("Scan entire GitHub org? (y/N): ").lower() == "y":
                org = input("Organization name: ")
            deep_scan = input("Deep GitHub scan? (y/N): ").lower() == "y"
            verify_ai = input("Verify leaks with AI? (y/N): ").lower() == "y"
            active_verify = input("Active token verify? (y/N): ").lower() == "y"
            notify = input("Send Telegram/Discord alerts? (y/N): ").lower() == "y"
            results = SearchManager.run_full_auto_mode(
                keyword,
                employees=employees,
                verify_ai=verify_ai,
                active_verify=active_verify,
                notify=notify,
                tokens=tokens,
                organization=org,
                deep_scan=deep_scan,
            )
            if results:
                print_results(results)
                report_path = generate_html_report(results, path="results.html")
                print(f"Report saved to {report_path}")
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
                report_path = generate_html_report(results, path="results.html")
                print(f"Report saved to {report_path}")
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
