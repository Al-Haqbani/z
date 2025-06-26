# EmploLeaksGuardian

EmploLeaksGuardian is a lightweight Python tool that scans multiple platforms for leaked API keys or secrets. It now searches GitHub, **GitLab**, **Bitbucket**, DockerHub, HuggingFace, NPM, PyPI, Reddit, Pastebin, **SwaggerHub**, **GrayHatWarfare buckets**, **Gitea instances**, and even public **GitHub Gists** by performing real HTTP requests with randomized user-agents and automatic backoff. HTTP requests now use a 30-second timeout and retry up to eight times to avoid API timeouts.
It can also run **TruffleHog** scans on repositories to leverage their advanced secret hunting heuristics.

It also includes a **Recon module** that discovers references to your company across third‑party services like Slack or Google Docs. These URLs are gathered from live queries and the Wayback Machine, then verified asynchronously so you know whether each link is still reachable.

This project was originally created by **محمد الحقباني** to help security researchers uncover leaks and protect their organizations. The goal is to build the strongest global tool of its kind. Please use it responsibly for legitimate security testing only.
In addition, a **Smart JS Scanner** can crawl JavaScript files from any domain (including optional subdomains and archived copies via the Wayback Machine).

When commit scanning is enabled, GitHub results also include leaked secrets found in commit messages and diffs, allowing detection of tokens in deleted files.
An optional **Deep Scan** mode searches GitHub issues in addition to code and commits for more thorough coverage. You can also enable **Full Repo Scan** to crawl every file in selected repositories or entire organizations, ensuring nothing is missed. A new **Wayback Repo** option downloads archived versions of repository files from the Wayback Machine so even deleted content is inspected. You can further enable **commit history**, **pull request** and **release** scanning so diffs, changelogs and deleted files are inspected for secrets as well.
GitHub searches leverage a curated list of "dorks" sourced from the public [GitDorker](https://github.com/obheda12/GitDorker/) project. These prebuilt queries combine with your keyword to uncover common secret patterns across GitHub.

The tool ships with a list of over 200 regex patterns derived from the public database at [secrets.ninja](https://secrets.ninja/) and expanded with rules from [iwatchr.iscan.today](https://iwatchr.iscan.today/). These patterns cover a wide variety of API keys and tokens to improve detection accuracy. Additional generic patterns inspired by [Search for all leaked keys](https://github.com/Lu3ky13/Search-for-all-leaked-keys-secrets-using-one-regex-) help detect common password or API key assignments.
Recent updates also integrate private key signatures (RSA, DSA, EC and PGP) and JWT formats. All patterns are combined into a single master regex so scanning large files is much faster while still labeling each leak by type.
Additional patterns now detect Supabase, Vercel, Railway, Kaggle, Asana and Bugcrowd tokens for even broader coverage. Slack bot tokens, HuggingFace access tokens and Zendesk secrets are also included so leaks from those services are flagged.
New patterns also detect GitHub app secrets, GitHub Enterprise PATs, Telegram API credentials and ChatGPT API keys. We incorporated leak types highlighted on the **@arshadkazmi42** feed (creator of iScan.today) so tokens like *Mistral AI keys*, *Zoom JWTs* and *Discord webhooks* are recognized as well.

To further reduce false positives, matches are filtered using a small entropy check. Short or low‑entropy strings are ignored unless they resemble real credentials. Generic patterns also require at least one digit so ordinary words like `generator-app` aren't flagged.

It can optionally search employees automatically by inspecting both the contributors and commit authors of a repository you provide. Their public gists can be scanned as well when the **scan gists** option is enabled. You can also search an entire GitHub organization in one go by supplying an org name. A modern web interface on `localhost:8000` lets you run scans and view results. The UI is styled with Bootstrap for a clean look and now lets you toggle AI verification, commit scanning and silent mode directly from your browser. A dedicated `/scans` page lists all scans with their status.
When employee scanning is enabled, DockerHub is also queried for repositories owned by those usernames. GitHub scans additionally parse `Dockerfile` instructions and automatically search any referenced images on DockerHub so leaks in container descriptions can be found at the same time.
The dashboard keeps a history of all scans and shows whether each one is still running or finished. You can open a **Live** view to watch results stream in as they are discovered, or view the final report once the scan is done.
Results appear on the page in real time thanks to server‑sent events, so you can monitor a scan while it is still running.
The web dashboard adopts a custom dark gradient style with animated cards for a sleeker look. Rows fade in as leaks appear for a smoother experience. The moving gradient background gives each page a dynamic feel.
Full Auto Mode executes all searchers concurrently to accelerate large scans.
You can restrict which platforms run by providing a comma-separated list with
`--platforms github,gitlab` or entering that list when prompted.
For quick checks you can enable the **Top Leaks** option, which searches GitHub for ten of the most commonly leaked API tokens such as AWS, Slack and HuggingFace keys.
Leak results may also be verified by a free AI classifier. When enabled from the prompts or the web form, each detected token is checked with a lightweight model from HuggingFace to reduce false positives. For even more accuracy you can enable *active verification*, which issues small HTTP requests (via `curl`) to confirm that URLs are reachable or that tokens remain valid by calling their APIs. Supported checks now cover GitHub, **GitLab**, Slack, Discord, Telegram, HuggingFace, **OpenAI**, **Mistral AI** and **Zoom** tokens, **Vercel**, **Railway**, **Asana**, **Bugcrowd**, **Supabase**, **DigitalOcean**, **Stripe**, **Notion**, **Kaggle**, **Anthropic**, **Gemini**, **Replicate** and **Stability AI**, and **Salesforce** keys as well as **Google** API credentials.
The CLI now highlights the severity of each finding in color for quick triage.
When active verification is enabled, each leak is tested with a tiny HTTP request. Unverified results are discarded so the report only lists tokens that still work.
Public GitHub Gists are also scanned to catch secrets that might be shared outside repositories, including gists owned by employees when that option is selected.

For deeper analysis you can enable the **TruffleHog** searcher, which runs the open source tool over selected repositories to analyze their full commit history.

## Architecture Overview

The project follows a modular layout so new platforms or features can be added
easily. The main CLI lives in `emploleaks.py` and delegates work to the
`SearchManager`. Each supported service implements a `*Searcher` class under the
`core/` directory. Utility helpers reside in `utils/`, while reporting logic is
kept in `output/` and `report_generator/`. A lightweight web interface is
provided via `webapp.py` and an optional React dashboard can be built from the
`frontend/` folder. Reports and the SQLite database are stored under `reports/`
by default. See the directory tree below for a high level view:

```
EmploLeaksGuardian8/
├── emploleaks.py
├── core/               # searchers and detection helpers
├── utils/              # HTTP helpers, logging, subdomain enum
├── output/             # terminal table output
├── report_generator/   # HTML report creation
├── drive_upload/       # Google Drive integration
├── is_scanner/         # Smart JS scanner
└── frontend/           # optional React dashboard
```


## Installation

Clone the repository and install the dependencies:

```bash
git clone https://github.com/Al-Haqbani/EmploLeaksGuardian.git
cd EmploLeaksGuardian
pip install -r requirements.txt
```


## Usage

```
python3 emploleaks.py
```
Install the dependencies first:

```
pip install -r requirements.txt
```

### Configuration file

You can store default tokens and options in a JSON config file. By default the
tool looks for `config.json` in the current directory or the path specified in
the `EMPLOLEAKS_CONFIG` environment variable. You can also pass a custom path
with `--config <file>`.

Example `config.json`:

```json
{
  "github_token": "ghp_yourtoken",
  "gitlab_token": "",
  "swaggerhub_token": "",
  "bitbucket_token": "",
  "grayhat_token": "",
  "gitea_token": ""
}
```

Any value left blank will still prompt at runtime. Using a config file lets you
avoid retyping tokens for every scan.

At startup you will be asked for API tokens for GitHub, GitLab, **Bitbucket**, SwaggerHub and GrayHatWarfare.
You can provide **multiple GitHub tokens** separated by commas to avoid rate limits—the
tool will rotate between them automatically. If all tokens hit the limit the
searcher sleeps until the earliest reset time and then resumes from where it
left off. Providing tokens greatly improves results on
those platforms. If you skip a token or provide an invalid one, searches on that platform
may return no results and you may see warning messages. GitHub's code search API in
particular **requires** authentication. When no GitHub token is supplied the tool now warns
and skips GitHub results instead of timing out.

Follow the prompts to perform a normal scan on a chosen platform, run the Smart JS scan, or run full auto mode across all supported platforms. When employee scanning is enabled you will be asked for a repository name (owner/repo) and the tool will automatically gather contributor usernames. If you disable employee scanning you may still provide a repository path so only that repo is searched. Results now stream to the terminal immediately whenever a leak is found, and the same events are forwarded to the web UI if it is running. This lets you monitor progress in both places at once. After each scan a timestamped HTML report and JSON file are saved under the directory specified by the `EMPLOLEAKS_OUTPUT` environment variable (default `reports`). All findings are also stored in a small SQLite database at `reports/scan_results.db` (override with `EMPLOLEAKS_DB`).  You can also launch the web interface from the menu, which mirrors CLI scans automatically.
All console output is saved to `logs/runtime.log` for later review.

### Command line options

You can also run scans non-interactively:

```bash
python3 emploleaks.py -p github -k acme --full-auto --full-repo --commits --verify-ai
```

Use `python3 emploleaks.py --help` to see every available flag.
Passing `--docker` will include DockerHub searches alongside GitHub results.
Run `python3 emploleaks.py --list-patterns` to display the names of all built-in leak patterns.

If you enable **Full Repo Scan**, the GitHub searcher crawls every file in each selected repository (or the entire organization) rather than relying solely on the search API. This thorough mode may take significantly longer. The **Wayback Repo** option can additionally fetch archived snapshots of those files to detect secrets that were deleted from history. Optional switches allow scanning commit history, pull requests and employee gists too, and a **Top Leaks** mode queries GitHub for the most common API keywords like AWS, Slack, HuggingFace and Zendesk keys.
You can adjust the maximum number of concurrent search threads with `--threads N`.
To limit full-auto scans to certain platforms you can pass a comma-separated
list with `--platforms github,gitlab,dockerhub`.
You can also enable **Scan repository wiki** to inspect the project's wiki pages for leaks.
The new **Scan releases** option analyzes release descriptions so tokens leaked in changelogs are not missed.
The **Scan actions logs** option downloads GitHub Actions logs and inspects them for secrets leaked during CI runs.

To use the web interface separately, run:

```
python3 webapp.py
```

While a scan runs, results stream live to the page using server‑sent events, so you can watch leaks appear in real time without waiting for the full scan to finish.

The refreshed dark interface (now using the **Cyborg** Bootswatch theme) shows live results in color-coded tables with running counters for High, Medium, Low and Info leaks. Rows fade in smoothly and you can filter by platform, severity or keyword while the scan runs. A list in the sidebar tracks every repository and turns green once its scan is finished. The CLI also prints progress messages such as `Scanning owner/repo (3/10)` so you know which repository is being processed.
Progress events now also include the total number of leaks found so far, letting
you watch the count rise in real time both in the terminal and the web
dashboard. Other platforms such as DockerHub, PyPI and NPM emit similar progress
updates so you can see which repository or package is being scanned at any
moment. Public Gists and Recon scans now report their progress as well so the
interface shows exactly which gist or external domain is being processed.

The results page includes a **Map** link that opens an interactive graph view.
Nodes represent repositories, files and individual leaks. Progress events add
new nodes while scanning so you can watch connections form in real time similar
to a Maltego graph. Repositories change color once finished and files appear as
intermediate nodes between the repo and each leak.
Platform icons accompany repositories on the map and next to each result row so
it's clear whether a leak came from GitHub, GitLab, DockerHub or another source.
If the same username is discovered across multiple platforms (for example a GitHub
account and matching DockerHub namespace), the map links those accounts so you can
see relationships between services at a glance.

For a richer experience, a React.js dashboard powered by **Material‑UI** lives under the `frontend` directory. After building it with `npm run build`, browse to `/app/` on the Flask server. This single‑page app connects to the `/stream/<scan_id>` endpoint via **EventSource** to show which repository is being scanned right now. It features pause, resume and cancel buttons, animated progress indicators and a summary of repositories scanned and leak counts. Completed scans automatically generate downloadable HTML and JSON reports.
AI verification requires the optional `transformers` and `torch` packages. Install them with:

```
pip install transformers torch
```

The main dependencies (listed in `requirements.txt`) are required to run the
scanner. The optional packages above are only needed if you enable the AI
verification feature from the prompts.

If you set the environment variables `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` or
`DISCORD_WEBHOOK_URL`, the tool can send alerts when leaks are discovered.
To query GrayHatWarfare buckets you must supply a valid `GRAYHAT_TOKEN` when prompted or as an environment variable.
To scan private Gitea servers set `GITEA_URL` to the instance's API base URL and supply an access token when prompted.

If your network requires a proxy, set the `EMPLOLEAKS_PROXY` environment variable
to the proxy URL. All HTTP requests will then use this proxy, which can help
avoid blocks and provide extra anonymity.

### Smart JS Scanner

The third menu option lets you scan a website's JavaScript files. You can choose
to enumerate subdomains, fetch archived files from the Wayback Machine and even
run [LinkFinder](https://github.com/GerbenJavado/LinkFinder) for deeper crawling.

```bash
python3 emploleaks.py
# choose "Smart JS Scan" from the menu
```

This implementation provides a basic framework. Each searcher can be extended or improved by customizing the logic in the `core/` directory. Support for **GitLab** and **SwaggerHub** has been added to broaden coverage across more platforms.

### Recon Module

Select "Recon Scan" from the menu to gather URLs mentioning your target on popular third-party platforms. The module queries the Wayback Machine for historical hits on domains like Slack and Google Docs, then verifies each link concurrently to record its current HTTP status. Recon results appear alongside other findings and can be filtered by status code in the web UI.
You can customize the domains checked by editing `data/recon_services.json`.

---

EmploLeaksGuardian is distributed for educational and defensive security purposes only. The author does **not** take responsibility for any misuse of this project.
