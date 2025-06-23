import sys
import threading
import webbrowser
import time
import queue
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
    from webapp import app as web_app, SCAN_HISTORY, SCAN_QUEUES
except Exception:
    web_app = None
    SCAN_HISTORY = {}
    SCAN_QUEUES = {}


_web_thread = None

def _create_cli_scan(keyword):
    """Create a scan entry so the web UI can display CLI scans."""
    if not web_app:
        return None, None
    scan_id = str(int(time.time()))
    q = queue.Queue()
    SCAN_QUEUES[scan_id] = q
    SCAN_HISTORY[scan_id] = {"keyword": keyword, "results": [], "status": "running"}
    return scan_id, q

def _finalize_cli_scan(scan_id, results):
    if not web_app or scan_id is None:
        return
    SCAN_HISTORY[scan_id]["results"] = results
    SCAN_HISTORY[scan_id]["status"] = "done"
    SCAN_QUEUES.get(scan_id, queue.Queue()).put(None)

def start_web_ui():
    """Launch the Flask web interface in a background thread"""
    global _web_thread
    if not web_app or _web_thread and _web_thread.is_alive():
        return
    def _run():
        web_app.run(port=8000)
    _web_thread = threading.Thread(target=_run, daemon=True)
    _web_thread.start()
    try:
        webbrowser.open("http://127.0.0.1:8000")
    except Exception:
        pass

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
            start_web_ui()
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
            history = input("Scan commit history? (y/N): ").lower() == "y"
            prs = input("Scan pull requests? (y/N): ").lower() == "y"
            top_leaks = input("Search top leaks? (y/N): ").lower() == "y"
            wayback = input("Scan Wayback snapshots? (y/N): ").lower() == "y"
            include_buckets = input("Search open buckets? (y/N): ").lower() == "y"
            verify_ai = input("Verify leaks with AI? (y/N): ").lower() == "y"
            active_verify = input("Active token verify? (y/N): ").lower() == "y"
            notify = input("Send Telegram/Discord alerts? (y/N): ").lower() == "y"
            scan_id, q = _create_cli_scan(keyword)

            def cb(item, idx):
                if q:
                    q.put(item)
                print_result(item, idx)

            def prog(info):
                if q:
                    info["_event"] = "progress"
                    q.put(info)
                print_progress(info)

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
                scan_history=history,
                scan_prs=prs,
                top_common=top_leaks,
                scan_wayback=wayback,
                result_callback=cb,
                progress_callback=prog,
            )
            _finalize_cli_scan(scan_id, results)
            if results:
                print_results(results)
                report_path = generate_html_report(results, path="results.html")
                save_json_report(results, path="results.json")
                print(f"Report saved to {report_path} and results.json")
            else:
                print("No leaks found.")
        elif choice == "2":
            start_web_ui()
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
            history = input("Scan commit history? (y/N): ").lower() == "y"
            prs = input("Scan pull requests? (y/N): ").lower() == "y"
            top_leaks = input("Search top leaks? (y/N): ").lower() == "y"
            wayback = input("Scan Wayback snapshots? (y/N): ").lower() == "y"
            include_buckets = input("Search open buckets? (y/N): ").lower() == "y"
            verify_ai = input("Verify leaks with AI? (y/N): ").lower() == "y"
            active_verify = input("Active token verify? (y/N): ").lower() == "y"
            notify = input("Send Telegram/Discord alerts? (y/N): ").lower() == "y"
            temp_tokens = dict(tokens)
            if not include_buckets:
                temp_tokens["grayhat"] = None
            scan_id, q = _create_cli_scan(keyword)

            def cb(item, idx):
                if q:
                    q.put(item)
                print_result(item, idx)

            def prog(info):
                if q:
                    info["_event"] = "progress"
                    q.put(info)
                print_progress(info)

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
                scan_history=history,
                scan_prs=prs,
                top_common=top_leaks,
                scan_wayback=wayback,
                result_callback=cb,
                progress_callback=prog,
            )
            _finalize_cli_scan(scan_id, results)
            if results:
                print_results(results)
                report_path = generate_html_report(results, path="results.html")
                save_json_report(results, path="results.json")
                print(f"Report saved to {report_path} and results.json")
            else:
                print("No leaks found.")
        elif choice == "3":
            start_web_ui()
            from is_scanner.js_scanner import run_smart_scan

            domain = input("Domain: ")
            sub = input("Enumerate subdomains? (y/N): ").lower() == "y"
            use_wb = input("Use Wayback? (Y/n): ").lower() != "n"
            use_lf = input("Run LinkFinder? (y/N): ").lower() == "y"
            scan_id, q = _create_cli_scan(domain)
            found = run_smart_scan(domain, include_subdomains=sub, use_wayback=use_wb, use_linkfinder=use_lf)
            results = []
            for item in found:
                res = {
                    "source": "JavaScript",
                    "file": item["url"],
                    "leak_type": item["leak_type"],
                    "value": item["value"],
                }
                results.append(res)
                if q:
                    q.put(res)
            _finalize_cli_scan(scan_id, results)
            if results:
                print_results(results)
                report_path = generate_html_report(results, path="results.html")
                save_json_report(results, path="results.json")
                print(f"Report saved to {report_path} and results.json")
            else:
                print("No leaks found.")
        elif choice == "4":
            start_web_ui()
            keyword = input("Company name or domain: ")
            scan_id, q = _create_cli_scan(keyword)

            def cb(item, idx):
                if q:
                    q.put(item)
                print_result(item, idx)

            results = SearchManager.start_search(
                "recon",
                keyword,
                tokens=tokens,
                result_callback=cb,
            )
            _finalize_cli_scan(scan_id, results)
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
