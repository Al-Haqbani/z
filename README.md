# EmploLeaksGuardian

EmploLeaksGuardian is a lightweight Python tool that scans multiple platforms for leaked API keys or secrets. It now searches GitHub, **GitLab**, **Bitbucket**, DockerHub, HuggingFace, NPM, PyPI, Reddit, Pastebin, **SwaggerHub**, **GrayHatWarfare buckets**, **Gitea instances**, even public **GitHub Gists**, and archived **JavaScript files** via the new `jsfile` platform. All requests use randomized user-agents and automatic backoff with a 30-second timeout and up to eight retries.
It can also run **TruffleHog** scans on repositories to leverage their advanced secret hunting heuristics. A **Short URL** mode queries the GrayHatWarfare shorteners API to find links referencing your company or domains.

It also includes a **Recon module** that discovers references to your company across third‑party services like Slack or Google Docs. These URLs are gathered from live queries and the Wayback Machine, then verified asynchronously so you know whether each link is still reachable.

This project was originally created by **محمد الحقباني** to help security researchers uncover leaks and protect their organizations. The goal is to build the strongest global tool of its kind. Please use it responsibly for legitimate security testing only. The author assumes no liability for misuse of this software.
In addition, a **Smart JS Scanner** can crawl JavaScript files from any domain (including optional subdomains and archived copies via the Wayback Machine).

When commit scanning is enabled, GitHub results also include leaked secrets found in commit messages and diffs, allowing detection of tokens in deleted files.
An optional **Deep Scan** mode searches GitHub issues in addition to code and commits for more thorough coverage. You can also enable **Full Repo Scan** to crawl every file in selected repositories or entire organizations, ensuring nothing is missed. A new **Wayback Repo** option downloads archived versions of repository files from the Wayback Machine so even deleted content is inspected. You can further enable **commit history**, **pull request** and **release** scanning so diffs, changelogs and deleted files are inspected for secrets as well.
GitHub searches leverage a curated list of "dorks" sourced from the public [GitDorker](https://github.com/obheda12/GitDorker/) project. These prebuilt queries combine with your keyword to uncover common secret patterns across GitHub.
There is also a Short URL scanner that queries GrayHatWarfare's shorteners API and matches expanded links against your company name or domains.  When available the scanner records the **creation time** and **size** of each short link so you can gauge how old it is and whether it hosts a large payload.  If you run scans from the web interface, the tool also captures a small **screenshot** of each expanded URL so you can preview where a short link leads without opening it.

The tool ships with a list of over 200 regex patterns derived from the public database at [secrets.ninja](https://secrets.ninja/) combined with other community-maintained rules. These patterns cover a wide variety of API keys and tokens to improve detection accuracy. Additional generic patterns inspired by [Search for all leaked keys](https://github.com/Lu3ky13/Search-for-all-leaked-keys-secrets-using-one-regex-) help detect common password or API key assignments.
Recent updates also integrate private key signatures (RSA, DSA, EC and PGP) and JWT formats. All patterns are combined into a single master regex so scanning large files is much faster while still labeling each leak by type.
Additional patterns now detect Supabase, Vercel, Railway, Kaggle, Asana and Bugcrowd tokens for even broader coverage. Slack bot tokens, HuggingFace access tokens and Zendesk secrets are also included so leaks from those services are flagged. Recent updates add **Anthropic** and **Gemini** API keys so modern AI services are covered.
New patterns also detect GitHub app secrets, GitHub Enterprise PATs, Telegram API credentials and ChatGPT API keys. We incorporated leak types shared by security researchers so tokens like *Mistral AI keys*, *Zoom JWTs* and *Discord webhooks* are recognized as well.
Okta API tokens and Azure client secrets are included too, expanding coverage of enterprise services. Trello and Dropbox API tokens have also been added to the detection rules. Recent updates extend coverage to **Ollama** and **Perplexity AI** keys as well.

To further reduce false positives, matches are filtered using a small entropy check. Short or low‑entropy strings are ignored unless they resemble real credentials. Generic patterns also require at least one digit so ordinary words like `generator-app` aren't flagged.

It can optionally search employees automatically. When the repository belongs to an organization, usernames are pulled from the organization's **People** page so only actual employees are scanned (falling back to collaborators if needed). Their public gists can be scanned as well when the **scan gists** option is enabled. You can also search an entire GitHub organization in one go by supplying an org name. A modern web interface on `localhost:8000` lets you run scans and view results. The UI is styled with Bootstrap for a clean look and now lets you toggle AI verification, commit scanning and silent mode directly from your browser. A dedicated `/scans` page lists all scans with their status.
When employee scanning is enabled, DockerHub is also queried for repositories owned by those usernames. GitHub scans additionally parse `Dockerfile` instructions and automatically search any referenced images on DockerHub so leaks in container descriptions can be found at the same time. DockerHub scanning now fetches each tag's image metadata as well as repository READMEs so tokens hidden in build layers are discovered.
The dashboard keeps a history of all scans and shows whether each one is still running or finished. Start and finish times are displayed so you can track when a scan began and ended. You can open a **Live** view to watch results stream in as they are discovered. A progress bar lists each repository as it completes and you can **pause**, **resume**, or **cancel** the scan mid‑flight. Once finished you can download the HTML/JSON reports for that scan.
Results appear on the page in real time thanks to server‑sent events, so you can monitor a scan while it is still running.
The web dashboard adopts a dark gradient style with a purple accent and animated cards for a sleek look. Rows fade in as leaks appear for a smoother experience. The progress bar now uses a purple‑to‑orange gradient and displays the current repository name and percentage so you can see exactly what is being scanned.
Leak rows include color-coded severity badges (red for High, yellow for Medium, blue for Low) so you can gauge risk at a glance. The **Active** column also shows a green or gray badge indicating whether the token was verified successfully.
Animations are powered by the lightweight effects from [reactbits.de](https://reactbits.de), giving buttons and cards subtle motion.
Scan history rows also use Reactbits `FadeIn` so entries slide gracefully into view while scans run.
Full Auto Mode executes all searchers concurrently to accelerate large scans.
You can restrict which platforms run by providing a comma-separated list with
`--platforms github,gitlab` or entering that list when prompted.
For quick checks you can enable the **Top Leaks** option, which searches GitHub for ten of the most commonly leaked API tokens such as AWS, Slack and HuggingFace keys.
Leak results may also be verified by a free AI classifier. When enabled from the prompts or the web form, each detected token is checked with a lightweight model from HuggingFace to reduce false positives. For even more accuracy you can enable *active verification*, which issues small HTTP requests (via `curl`) to confirm that URLs are reachable or that tokens remain valid by calling their APIs. Supported checks now cover GitHub, **GitLab**, Slack, Discord, Telegram, HuggingFace, **OpenAI**, **Mistral AI** and **Zoom** tokens, **Vercel**, **Railway**, **Asana**, **Bugcrowd**, **Supabase**, **DigitalOcean**, **Stripe**, **Notion**, **Kaggle**, **Cohere**, **Anthropic**, **Gemini**, **Replicate** and **Stability AI**, **Salesforce**, and **Facebook** keys as well as **Google** API credentials.
The CLI now highlights the severity of each finding in color for quick triage.
Each built‑in regex pattern carries a default severity (high or medium) and that
value is used when displaying results.
When active verification is enabled, each leak is tested with a tiny HTTP request. Unverified results are discarded so the report only lists tokens that still work.
Verified leaks include a small **PoC** command showing the curl request that confirmed the token is valid.
All verification requests go through the same backoff helper used for normal HTTP traffic,
rotating user agents and retrying automatically so network hiccups don't cause false negatives.
Public GitHub Gists are also scanned to catch secrets that might be shared outside repositories, including gists owned by employees when that option is selected.

Each leak is also assigned a simple **risk score** based on its severity, whether
the token is still active and how many times it appears across platforms. The
score ranges from 0–100 and lets you prioritize which findings need attention
first.

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
pip install -r requirements.txt  # installs requests, pyyaml, flask and more
```

### Quickstart

Instead of manually installing packages you can run:

```bash
./setup.sh
```

This installs all requirements and prints a command to launch the tool. To
start the web interface immediately use:

```bash
./run.sh
```

### Docker

Alternatively build a Docker image and run it in an isolated container:

```bash
docker build -t emploleaks .
docker run --rm -it emploleaks
```



## Usage

```
python3 -m emploleaks
```
Install the dependencies first:

```
pip install -r requirements.txt
pip install -e .  # install as package
```

Run `python3 emploleaks.py --bugbounty` to print the list of bug bounty programs
loaded from `data/bugbounty_programs.json` (now over 100 entries).
In the web interface a **Bug Bounty** link opens a table of all programs with a
**Hunt it?** button. Clicking it shows the program scope and any known GitHub
repositories so you can jump directly to targets.

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

At startup you will be asked for API tokens for GitHub, GitLab, **Bitbucket**, SwaggerHub, GrayHatWarfare and the **Shorteners** API used for scanning short URLs.
You can provide **multiple GitHub tokens** separated by commas to avoid rate limits—the
tool will rotate between them automatically. If all tokens hit the limit the
searcher sleeps until the earliest reset time and then resumes from where it
left off. Providing tokens greatly improves results on
those platforms. If you skip a token or provide an invalid one, searches on that platform
may return no results and you may see warning messages. GitHub's code search API in
particular **requires** authentication. When no GitHub token is supplied the tool now warns
and skips GitHub results instead of timing out.

Follow the prompts to perform a normal scan on a chosen platform, run the Smart JS scan, or run full auto mode across all supported platforms. When employee scanning is enabled you will be asked for a repository name (owner/repo) and the tool will automatically gather contributor usernames. If you disable employee scanning you may still provide a repository path so only that repo is searched. Results now stream to the terminal immediately whenever a leak is found, and the same events are forwarded to the web UI if it is running. After each scan a timestamped HTML report, JSON file, and PDF file are saved under the directory specified by the `EMPLOLEAKS_OUTPUT` environment variable (default `reports`). All findings are also stored in a small SQLite database at `reports/scan_results.db` (override with `EMPLOLEAKS_DB`). Optionally, the raw results can be uploaded to **jsontr.ee** to share an interactive JSON map. You can also launch the web interface from the menu, which mirrors CLI scans automatically. When started from the CLI, the interface opens automatically on http://localhost:8000 so you can follow progress live.
All console output is saved to `logs/runtime.log` for later review.
Set the `EMPLOLEAKS_THREADS` environment variable to control the default number
of concurrent threads used in full-auto mode.
Set `EMPLOLEAKS_LOG_LEVEL` (e.g. `DEBUG`, `INFO`, `WARNING`) to change
the verbosity of these logs if you need more or less detail.
`EMPLOLEAKS_TIMEOUT` and `EMPLOLEAKS_RETRIES` can adjust HTTP timeouts and retry
counts for all network requests if you need slower or more persistent scanning.
If you have your own JSON file of regex rules, set `EMPLOLEAKS_EXTRA_PATTERNS`
to the file path so those patterns are loaded automatically at startup.

### Repository wordlists

A sample list of common GitHub repositories is provided at
`data/repo_wordlist.txt`. You can pass this file to the wordlist generator
with `--wordlist` to create a custom dictionary containing repository names such
as `Googleai` and `Sallaapp`. These wordlists are useful for brute forcing or
mass searching tools that require candidate repository names.

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

Pass `--host 0.0.0.0` if you need to reach the dashboard from another device on your network.

While a scan runs, results stream live to the page using server‑sent events, so you can watch leaks appear in real time without waiting for the full scan to finish.

The refreshed dark interface (now using the **Cyborg** Bootswatch theme) shows live results in color-coded tables with running counters for High, Medium, Low and Info leaks. Rows fade in smoothly and you can filter by platform, severity or keyword while the scan runs. A list in the sidebar tracks every repository and turns green once its scan is finished. The CLI also prints progress messages such as `Scanning owner/repo (3/10)` so you know which repository is being processed.
Each new leak also triggers a small toast notification in the corner so you don't miss important findings while navigating the dashboard.
The interface now loads the Inter font and cards feature soft shadows for a polished look.
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
To scan short URLs you will also need a `SHORTURL_TOKEN` from GrayHatWarfare.
To scan private Gitea servers set `GITEA_URL` to the instance's API base URL and supply an access token when prompted.

If your network requires a proxy, set the `EMPLOLEAKS_PROXY` environment variable
to the proxy URL. All HTTP requests will then use this proxy, which can help
avoid blocks and provide extra anonymity.

### Smart JS Scanner

A **Smart JS Scanner** can crawl a website's JavaScript files. You can
enumerate subdomains, fetch archived files from the Wayback Machine and even run
[LinkFinder](https://github.com/GerbenJavado/LinkFinder) for deeper crawling. It
also extracts hidden paths and repository links from the scripts so you can map
potential endpoints in addition to leaked tokens.
For convenience this logic is also available as a standalone platform named
`jsfile` so you can include archived JavaScript scanning when running normal or
full‑auto scans. Simply choose `jsfile` as the platform and supply the target
domain.
A fourth option allows scanning a list of JavaScript URLs stored in a text file.

```bash
python3 emploleaks.py
# choose "Smart JS Scan" from the menu
```

Alternatively, select "JS File List Scan" and provide a text file containing
JavaScript URLs to scan:

```bash
python3 emploleaks.py
# choose "JS File List Scan" and enter the path to urls.txt
```

This implementation provides a basic framework. Each searcher can be extended or improved by customizing the logic in the `core/` directory. Support for **GitLab** and **SwaggerHub** has been added to broaden coverage across more platforms.

### Recon Module

Select "Recon Scan" from the menu to gather URLs mentioning your target on popular third-party platforms. The module queries the Wayback Machine and **urlscan.io** for historical hits on domains like Slack and Google Docs, then verifies each link concurrently to record its current HTTP status. Recon also enumerates subdomains of your target and scans their JavaScript for hidden paths or repository links. All URLs are verified and shown with status codes. Results appear alongside other findings and can be filtered by status code in the web UI.
You can customize the domains checked by editing `data/recon_services.json` and enable subdomain enumeration using the `scan_subdomains` option.

### Bug bounty program
The file `data/bugbounty_programs.json` lists a few public bug bounty programs with reporting links and scope. Run `python3 emploleaks.py --bugbounty` to print them so you know where to report leaks (many programs include GitHub repositories in scope).

### Plugin system
Custom search modules can be dropped into a `plugins/` folder as Python scripts or YAML files. A Python plugin should subclass `BasePlugin` from `utils.plugin_loader` and implement `search(keyword)` returning a list of leak dictionaries. YAML files may define a simple `name` and list of regex `patterns`. Use `--plugins path1,path2` to load them at runtime.
---

EmploLeaksGuardian is distributed for educational and defensive security purposes only. The author does **not** take responsibility for any misuse of this project.

### Monitoring scans
You can periodically rescan a keyword using the new `monitor.py` script. It reads your configuration and runs full-auto scans on a schedule. For example:
```bash
python3 monitor.py "acme corp" --interval 120 --config config.json
```
This will run a scan every two hours. Results are printed to the terminal and stored just like manual scans.
\nThe interface uses Poppins for headings and Inter for body text, giving it a polished high-end look.
