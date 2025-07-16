import argparse, time, schedule, os
from utils.config import load_config
from core.search_manager import SearchManager
from core.token_manager import get_token

def run_scan(keyword, tokens):
    print(f"Running scheduled scan for {keyword}")
    results = SearchManager.run_full_auto_mode(keyword, tokens=tokens)
    print(f"Scan complete: {len(results)} leaks")


def main():
    p = argparse.ArgumentParser(description="EmploLeaksGuardian monitor")
    p.add_argument('keyword', help='Keyword or repo to scan')
    p.add_argument('--interval', type=int, default=60, help='Minutes between scans')
    p.add_argument('--config', help='Path to config JSON')
    args = p.parse_args()
    cfg = load_config(args.config)
    tokens = {
        'github': get_token('GitHub', 'GITHUB_TOKEN', cfg.get('github_token')),
    }
    run_scan(args.keyword, tokens)
    schedule.every(args.interval).minutes.do(run_scan, args.keyword, tokens)
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == '__main__':
    main()
