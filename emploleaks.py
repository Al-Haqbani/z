import sys
import threading
import webbrowser
import time
import queue
import argparse
import os
from utils.logger import logger
from core.token_manager import get_token, get_github_token
from utils.config import load_config
from core.search_manager import SearchManager
from utils.database import init_db, record_scan, finish_scan, insert_leaks
from core.github_api import GitHubSearcher
from output.terminal_output import (
    print_results,
    print_result,
    print_progress,
)
from core.regex_patterns import (
    get_pattern_names,
    get_pattern_list,
    add_patterns_from_file,
)
from core.leak_detector import set_active_patterns
from report_generator.generate_report import generate_html_report, save_json_report

try:
    from webapp import app as web_app, SCAN_HISTORY, SCAN_QUEUES
except Exception:
    web_app = None
    SCAN_HISTORY = {}
    SCAN_QUEUES = {}


_web_thread = None


def parse_args():
    """Parse command line arguments if provided."""
    parser = argparse.ArgumentParser(description="EmploLeaksGuardian CLI")
    parser.add_argument(
        "-p", "--platform", help="Platform to scan (e.g. github, gitlab, gitea)"
    )
    parser.add_argument("-k", "--keyword", help="Search keyword")
    parser.add_argument("--full-auto", action="store_true", help="Run full auto mode")
    parser.add_argument("--smart-js", action="store_true", help="Run Smart JS scanner")
    parser.add_argument("--recon", action="store_true", help="Run recon scan")
    parser.add_argument("--org", help="GitHub organization to scan")
    parser.add_argument("--repo", help="Specific repository to scan")
    parser.add_argument(
        "--employees", action="store_true", help="Search employee accounts"
    )
    parser.add_argument("--deep", action="store_true", help="Enable deep GitHub scan")
    parser.add_argument("--full-repo", action="store_true", help="Full repository scan")
    parser.add_argument("--commits", action="store_true", help="Scan commit history")
    parser.add_argument("--prs", action="store_true", help="Scan pull requests")
    parser.add_argument(
        "--top-leaks", action="store_true", help="Use common leak queries"
    )
    parser.add_argument("--wayback", action="store_true", help="Scan Wayback snapshots")
    parser.add_argument(
        "--wiki", action="store_true", help="Scan repository wiki pages"
    )
    parser.add_argument(
        "--releases", action="store_true", help="Scan repository releases"
    )
    parser.add_argument(
        "--actions", action="store_true", help="Scan GitHub Actions logs"
    )
    parser.add_argument("--gists", action="store_true", help="Scan employee gists")
    parser.add_argument("--docker", action="store_true", help="Also scan DockerHub")
    parser.add_argument("--verify-ai", action="store_true", help="Verify leaks with AI")
    parser.add_argument(
        "--active-verify", action="store_true", help="Verify tokens via HTTP"
    )
    parser.add_argument(
        "--notify", action="store_true", help="Send Telegram/Discord alerts"
    )
    parser.add_argument("--web", action="store_true", help="Launch web interface")
    parser.add_argument("--config", help="Path to JSON config file")
    parser.add_argument("--proxy", help="HTTP proxy URL for all requests")
    parser.add_argument(
        "-t",
        "--threads",
        type=int,
        help="Maximum concurrent search threads in full-auto mode",
        default=0,
    )
    parser.add_argument(
        "--platforms",
        help="Comma-separated list of platforms for full-auto mode",
    )
    parser.add_argument(
        "--list-patterns", action="store_true", help="List available leak patterns"
    )
    parser.add_argument(
        "--patterns",
        help="Comma-separated pattern numbers or names to scan",
    )
    parser.add_argument(
        "--pattern-file",
        help="Path to JSON file with additional leak patterns",
    )
    return parser.parse_args()


def parse_pattern_selection(sel: str | None):
    """Convert user pattern selection to a list of pattern names."""
    if not sel:
        return None
    names = get_pattern_names()
    selected = []
    for part in sel.split(','):
        part = part.strip()
        if not part:
            continue
        if part.isdigit():
            idx = int(part)
            if 1 <= idx <= len(names):
                selected.append(names[idx - 1])
        elif part in names:
            selected.append(part)
    return selected or None


def _create_cli_scan(keyword):
    """Create a scan entry so the web UI can display CLI scans."""
    if not web_app:
        return None, None
    scan_id = str(int(time.time()))
    q = queue.Queue()
    SCAN_QUEUES[scan_id] = q
    SCAN_HISTORY[scan_id] = {"keyword": keyword, "results": [], "status": "running"}
    record_scan(scan_id, keyword, time.strftime("%Y-%m-%d %H:%M:%S"))
    return scan_id, q


def _finalize_cli_scan(scan_id, results):
    if scan_id is None:
        return
    finish_scan(scan_id, time.strftime("%Y-%m-%d %H:%M:%S"))
    insert_leaks(scan_id, results)
    logger.info("Scan %s completed with %d results", scan_id, len(results))
    if web_app:
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
    args = parse_args()
    if args.list_patterns:
        for idx, name in get_pattern_list():
            print(f"{idx}. {name}")
        return
    config = load_config(args.config)
    if args.pattern_file:
        from core.regex_patterns import add_patterns_from_file
        add_patterns_from_file(args.pattern_file)
    if args.proxy:
        os.environ["EMPLOLEAKS_PROXY"] = args.proxy
    print("EmploLeaksGuardian - Simple Leak Scanner")
    logger.info("Startup with args: %s", sys.argv[1:])
    init_db()
    github_token = get_token("GitHub", "GITHUB_TOKEN", config.get("github_token"))
    gitlab_token = get_token("GitLab", "GITLAB_TOKEN", config.get("gitlab_token"))
    swagger_token = get_token(
        "SwaggerHub", "SWAGGER_TOKEN", config.get("swaggerhub_token")
    )
    bitbucket_token = get_token(
        "Bitbucket", "BITBUCKET_TOKEN", config.get("bitbucket_token")
    )
    grayhat_token = get_token(
        "GrayHatWarfare", "GRAYHAT_TOKEN", config.get("grayhat_token")
    )
    gitea_token = get_token("Gitea", "GITEA_TOKEN", config.get("gitea_token"))
    tokens = {
        "github": github_token,
        "gitlab": gitlab_token,
        "bitbucket": bitbucket_token,
        "swaggerhub": swagger_token,
        "grayhat": grayhat_token,
        "trufflehog": github_token,
        "gitea": gitea_token,
    }

    selected_patterns = parse_pattern_selection(args.patterns)
    set_active_patterns(selected_patterns)

    # Non-interactive mode via arguments
    if any([args.platform, args.full_auto, args.smart_js, args.recon, args.web]):
        if args.web:
            start_web_ui()
        keyword = args.keyword or ""
        employees = None
        repo = args.repo
        if args.employees and repo:
            employees = GitHubSearcher.get_repo_employees(repo, github_token)

        if args.smart_js:
            from is_scanner.js_scanner import run_smart_scan

            results = []
            found = run_smart_scan(
                keyword,
                include_subdomains=False,
                use_wayback=args.wayback,
                use_linkfinder=args.deep,
            )
            for item in found:
                results.append(
                    {
                        "source": "JavaScript",
                        "file": item["url"],
                        "leak_type": item["leak_type"],
                        "value": item["value"],
                    }
                )
            if results:
                print_results(results)
            return

        if args.recon:
            results = SearchManager.start_search(
                "recon",
                keyword,
                tokens=tokens,
                patterns=selected_patterns,
            )
            if results:
                print_results(results)
            return

        if args.full_auto:
            results = SearchManager.run_full_auto_mode(
                keyword,
                employees=employees,
                organization=args.org,
                verify_ai=args.verify_ai,
                active_verify=args.active_verify,
                notify=args.notify,
                tokens=tokens,
                deep_scan=args.deep,
                full_scan=args.full_repo,
                repo=repo,
                scan_history=args.commits,
                scan_prs=args.prs,
                scan_gists=args.gists,
                top_common=args.top_leaks,
                scan_wayback=args.wayback,
                scan_wiki=args.wiki,
                scan_releases=args.releases,
                scan_actions=args.actions,
                include_docker=args.docker or employees is not None,
                follow_docker=args.docker or employees is not None,
                platforms=args.platforms.split(',') if args.platforms else None,
                max_threads=args.threads,
                patterns=selected_patterns,
            )
            if results:
                print_results(results)
            return

        if args.platform and args.keyword:
            results = SearchManager.start_search(
                args.platform,
                keyword,
                employees=employees,
                organization=args.org,
                verify_ai=args.verify_ai,
                active_verify=args.active_verify,
                notify=args.notify,
                tokens=tokens,
                deep_scan=args.deep,
                full_scan=args.full_repo,
                repo=repo,
                scan_history=args.commits,
                scan_prs=args.prs,
                scan_gists=args.gists,
                top_common=args.top_leaks,
                scan_wayback=args.wayback,
                scan_wiki=args.wiki,
                scan_actions=args.actions,
                include_docker=args.docker or args.employees,
                follow_docker=args.docker or args.employees,
                patterns=selected_patterns,
            )
            if args.platform == "github" and (args.docker or args.employees):
                docker_res = SearchManager.start_search(
                    "dockerhub",
                    keyword,
                    employees=employees,
                    tokens=tokens,
                    patterns=selected_patterns,
                )
                results.extend(docker_res)
            if results:
                print_results(results)
            return

    # Interactive menu fallback
    while True:
        print(
            "\nOptions:\n1. Normal Scan\n2. Full Auto Mode\n3. Smart JS Scan\n4. Recon Scan\n5. Web Interface\n6. Exit"
        )
        choice = input("Select option: ")
        if choice == "1":
            start_web_ui()
            platform = input(
                "Platform (github/gitlab/bitbucket/swaggerhub/dockerhub/huggingface/npm/pypi/reddit/pastebin/gist/grayhat/trufflehog/gitea): "
            )
            keyword = input("Keyword: ")
            use_emp = input("Search employee accounts? (y/N): ").lower() == "y"
            employees = None
            repo = None
            if use_emp:
                repo = input("GitHub repository (owner/repo) for lookup: ")
                only_emp = (
                    input(
                        "Search only employees mentioned in the company repository? (y/N): "
                    ).lower()
                    == "y"
                )
                if only_emp:
                    employees = GitHubSearcher.get_repo_employees(repo, github_token)
                else:
                    org_emp = input("Organization name for employee lookup (blank to skip): ").strip()
                    if org_emp:
                        employees = GitHubSearcher.get_org_members(org_emp, github_token)
                    if not employees:
                        emp_in = input("Employee usernames (comma separated): ").strip()
                        employees = [e.strip() for e in emp_in.split(',') if e.strip()] or None
            elif platform == "github":
                repo = (
                    input("Repository to scan (owner/repo, blank to skip): ").strip()
                    or None
                )
            org = None
            if input("Scan entire GitHub org? (y/N): ").lower() == "y":
                org = input("Organization name: ")
            deep_scan = input("Deep GitHub scan? (y/N): ").lower() == "y"
            full_repo = input("Full repo scan? (y/N): ").lower() == "y"
            history = input("Scan commit history? (y/N): ").lower() == "y"
            prs = input("Scan pull requests? (y/N): ").lower() == "y"
            gists = input("Scan employee gists? (y/N): ").lower() == "y"
            top_leaks = input("Search top leaks? (y/N): ").lower() == "y"
            pattern_in = ""
            if input("Do you want to select specific leak types? (y/N): ").lower() == "y":
                print("Available leak patterns:")
                for idx, name in get_pattern_list():
                    print(f"{idx}. {name}")
                pattern_in = input("Pattern numbers to scan (comma separated, blank for all): ").strip()
            selected_patterns = parse_pattern_selection(pattern_in)
            set_active_patterns(selected_patterns)
            wayback = input("Scan Wayback snapshots? (y/N): ").lower() == "y"
            wiki = input("Scan repository wiki? (y/N): ").lower() == "y"
            releases = input("Scan releases? (y/N): ").lower() == "y"
            actions = input("Scan actions logs? (y/N): ").lower() == "y"
            include_buckets = input("Search open buckets? (y/N): ").lower() == "y"
            docker_flag = input("Scan DockerHub too? (y/N): ").lower() == "y"
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
                employees_only=only_emp,
                verify_ai=verify_ai,
                active_verify=active_verify,
                notify=notify,
                tokens=tokens,
                organization=org,
                deep_scan=deep_scan,
                full_scan=full_repo,
                repo=repo,
                scan_history=history,
                scan_prs=prs,
                scan_gists=gists,
                top_common=top_leaks,
                scan_wayback=wayback,
                scan_wiki=wiki,
                scan_releases=releases,
                scan_actions=actions,
                include_docker=docker_flag or employees is not None,
                follow_docker=docker_flag or employees is not None,
                result_callback=cb,
                progress_callback=prog,
            )
            if platform == "github" and (docker_flag or employees):
                docker_results = SearchManager.start_search(
                    "dockerhub",
                    keyword,
                    employees=employees,
                    tokens=tokens,
                    patterns=selected_patterns,
                    result_callback=cb,
                    progress_callback=prog,
                )
                results.extend(docker_results)
            _finalize_cli_scan(scan_id, results)
            if results:
                print_results(results)
                report_path = generate_html_report(results)
                json_path = save_json_report(results)
                print(f"Report saved to {report_path} and {json_path}")
            else:
                print("No leaks found.")
        elif choice == "2":
            start_web_ui()
            keyword = input("Keyword: ")
            use_emp = input("Search employee accounts? (y/N): ").lower() == "y"
            employees = None
            repo = None
            if use_emp:
                repo = input("GitHub repository (owner/repo) for lookup: ")
                only_emp = (
                    input(
                        "Search only employees mentioned in the company repository? (y/N): "
                    ).lower()
                    == "y"
                )
                if only_emp:
                    employees = GitHubSearcher.get_repo_employees(repo, github_token)
                else:
                    org_emp = input("Organization name for employee lookup (blank to skip): ").strip()
                    if org_emp:
                        employees = GitHubSearcher.get_org_members(org_emp, github_token)
                    if not employees:
                        emp_in = input("Employee usernames (comma separated): ").strip()
                        employees = [e.strip() for e in emp_in.split(',') if e.strip()] or None
            else:
                repo = (
                    input("Repository to scan (owner/repo, blank to skip): ").strip()
                    or None
                )
            org = None
            if input("Scan entire GitHub org? (y/N): ").lower() == "y":
                org = input("Organization name: ")
            deep_scan = input("Deep GitHub scan? (y/N): ").lower() == "y"
            full_repo = input("Full repo scan? (y/N): ").lower() == "y"
            history = input("Scan commit history? (y/N): ").lower() == "y"
            prs = input("Scan pull requests? (y/N): ").lower() == "y"
            gists = input("Scan employee gists? (y/N): ").lower() == "y"
            top_leaks = input("Search top leaks? (y/N): ").lower() == "y"
            wayback = input("Scan Wayback snapshots? (y/N): ").lower() == "y"
            wiki = input("Scan repository wiki? (y/N): ").lower() == "y"
            releases = input("Scan releases? (y/N): ").lower() == "y"
            include_buckets = input("Search open buckets? (y/N): ").lower() == "y"
            docker_flag = input("Scan DockerHub too? (y/N): ").lower() == "y"
            verify_ai = input("Verify leaks with AI? (y/N): ").lower() == "y"
            active_verify = input("Active token verify? (y/N): ").lower() == "y"
            notify = input("Send Telegram/Discord alerts? (y/N): ").lower() == "y"
            platforms_in = (
                input("Platforms to scan (comma separated, blank for all): ")
                .strip()
            )
            platforms = [p.strip() for p in platforms_in.split(',') if p.strip()] if platforms_in else None
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
                employees_only=only_emp,
                verify_ai=verify_ai,
                active_verify=active_verify,
                notify=notify,
                tokens=temp_tokens,
                organization=org,
                deep_scan=deep_scan,
                full_scan=full_repo,
                repo=repo,
                scan_history=history,
                scan_prs=prs,
                scan_gists=gists,
                top_common=top_leaks,
                scan_wayback=wayback,
                scan_wiki=wiki,
                scan_releases=releases,
                scan_actions=actions,
                include_docker=docker_flag or employees is not None,
                result_callback=cb,
                progress_callback=prog,
                platforms=platforms,
                max_threads=args.threads,
            )
            _finalize_cli_scan(scan_id, results)
            if results:
                print_results(results)
                report_path = generate_html_report(results)
                json_path = save_json_report(results)
                print(f"Report saved to {report_path} and {json_path}")
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
            found = run_smart_scan(
                domain,
                include_subdomains=sub,
                use_wayback=use_wb,
                use_linkfinder=use_lf,
            )
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
                report_path = generate_html_report(results)
                json_path = save_json_report(results)
                print(f"Report saved to {report_path} and {json_path}")
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
                report_path = generate_html_report(results)
                json_path = save_json_report(results)
                print(f"Report saved to {report_path} and {json_path}")
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
