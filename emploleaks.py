import sys
from core.token_manager import get_github_token
from core.search_manager import SearchManager
from output.terminal_output import print_results

try:
    from webapp import app as web_app
except Exception:
    web_app = None


def main():
    print("EmploLeaksGuardian - Simple Leak Scanner")
    token = get_github_token()
    while True:
        print("\nOptions:\n1. Normal Scan\n2. Full Auto Mode\n3. Web Interface\n4. Exit")
        choice = input("Select option: ")
        if choice == "1":
            platform = input("Platform (github/dockerhub/huggingface/npm/pypi/reddit/pastebin): ")
            keyword = input("Keyword: ")
            use_emp = input("Search employee accounts? (y/N): ").lower() == "y"
            employees = None
            if use_emp:
                employees = input("Employee usernames (comma separated): ")
            results = SearchManager.start_search(platform, keyword, token=token, employees=employees)
            if results:
                print_results(results)
            else:
                print("No leaks found.")
        elif choice == "2":
            keyword = input("Keyword: ")
            use_emp = input("Search employee accounts? (y/N): ").lower() == "y"
            employees = None
            if use_emp:
                employees = input("Employee usernames (comma separated): ")
            results = SearchManager.run_full_auto_mode(keyword, token=token, employees=employees)
            if results:
                print_results(results)
            else:
                print("No leaks found.")
        elif choice == "3":
            if web_app:
                web_app.run(port=8000)
            else:
                print("Web interface not available (Flask missing)")
        elif choice == "4":
            sys.exit()
        else:
            print("Invalid option")


if __name__ == "__main__":
    main()
