import sys
from core.token_manager import get_github_token
from core.search_manager import SearchManager
from output.terminal_output import print_results


def main():
    print("EmploLeaksGuardian - Simple Leak Scanner")
    token = get_github_token()
    while True:
        print("\nOptions:\n1. Normal Scan\n2. Full Auto Mode\n3. Exit")
        choice = input("Select option: ")
        if choice == "1":
            platform = input("Platform (github/dockerhub/huggingface/npm/pypi/reddit/pastebin): ")
            keyword = input("Keyword: ")
            results = SearchManager.start_search(platform, keyword, token=token)
            if results:
                print_results(results)
            else:
                print("No leaks found.")
        elif choice == "2":
            keyword = input("Keyword: ")
            results = SearchManager.run_full_auto_mode(keyword, token=token)
            if results:
                print_results(results)
            else:
                print("No leaks found.")
        elif choice == "3":
            sys.exit()
        else:
            print("Invalid option")


if __name__ == "__main__":
    main()
