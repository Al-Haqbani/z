import sys
from core.token_manager import get_token, get_github_token
from core.search_manager import SearchManager
from core.github_api import GitHubSearcher
from output.terminal_output import (
    print_results,
    print_result,
    print_progress,
)
from report_generator.generate_report import generate_html_report, save_json_report

try:
    from webapp import app as web_app
except Exception:
    web_app = None


def main():
    print("EmploLeaksGuardian - Simple Leak Scanner")
    github_token = get_token("GitHub", "GITHUB_TOKEN")
    gitlab_token = get_token("GitLab", "GITLAB_TOKEN")
    swagger_token = get_token("SwaggerHub", "SWAGGER_TOKEN")
    grayhat_token = get_token("GrayHatWarfare", "GRAYHAT_TOKEN")
    tokens = {
        "github": github_token,
        "gitlab": gitlab_token,
        "swaggerhub": swagger_token,
        "grayhat": grayhat_token,
        "trufflehog": github_token,
    }
    while True:
        print("\nOptions:\n1. Normal Scan\n2. Full Auto Mode\n3. Smart JS Scan\n4. Recon Scan\n5. Web Interface\n6. Exit")
        choice = input("Select option: ")
        if choice == "1":
            platform = input("Platform (github/gitlab/swaggerhub/dockerhub/huggingface/npm/pypi/reddit/pastebin/gist/grayhat/trufflehog): ")
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
            full_repo = input("Full repo scan? (y/N): ").lower() == "y"
            wayback = input("Scan Wayback snapshots? (y/N): ").lower() == "y"
            include_buckets = input("Search open buckets? (y/N): ").lower() == "y"
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
                full_scan=full_repo,
                scan_wayback=wayback,
                result_callback=print_result,
                progress_callback=print_progress,
            )
            if results:
                print_results(results)
                report_path = generate_html_report(results, path="results.html")
                save_json_report(results, path="results.json")
                print(f"Report saved to {report_path} and results.json")
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
            full_repo = input("Full repo scan? (y/N): ").lower() == "y"
            wayback = input("Scan Wayback snapshots? (y/N): ").lower() == "y"
            include_buckets = input("Search open buckets? (y/N): ").lower() == "y"
            verify_ai = input("Verify leaks with AI? (y/N): ").lower() == "y"
            active_verify = input("Active token verify? (y/N): ").lower() == "y"
            notify = input("Send Telegram/Discord alerts? (y/N): ").lower() == "y"
            temp_tokens = dict(tokens)
            if not include_buckets:
                temp_tokens["grayhat"] = None
            results = SearchManager.run_full_auto_mode(
                keyword,
                employees=employees,
                verify_ai=verify_ai,
                active_verify=active_verify,
                notify=notify,
                tokens=temp_tokens,
                organization=org,
                deep_scan=deep_scan,
                full_scan=full_repo,
                scan_wayback=wayback,
                result_callback=print_result,
                progress_callback=print_progress,
            )
            if results:
                print_results(results)
                report_path = generate_html_report(results, path="results.html")
                save_json_report(results, path="results.json")
                print(f"Report saved to {report_path} and results.json")
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
                save_json_report(results, path="results.json")
                print(f"Report saved to {report_path} and results.json")
            else:
                print("No leaks found.")
        elif choice == "4":
            keyword = input("Company name or domain: ")
            results = SearchManager.start_search(
                "recon",
                keyword,
                tokens=tokens,
                result_callback=print_result,
            )
            if results:
                print_results(results)
                report_path = generate_html_report(results, path="results.html")
                save_json_report(results, path="results.json")
                print(f"Report saved to {report_path} and results.json")
            else:
                print("No URLs found.")
        elif choice == "5":
            if web_app:
                web_app.run(port=8000)
            else:
                print("Web interface not available (Flask missing)")
        elif choice == "6":
            sys.exit()
        else:
            print("Invalid option")


if __name__ == "__main__":
    main()
