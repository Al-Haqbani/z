# EmploLeaksGuardian

EmploLeaksGuardian is a lightweight Python tool that scans multiple platforms for leaked API keys or secrets. It now searches GitHub, **GitLab**, DockerHub, HuggingFace, NPM, PyPI, Reddit, Pastebin, **SwaggerHub**, **GrayHatWarfare buckets**, and even public **GitHub Gists** by performing real HTTP requests with randomized user-agents and automatic backoff. HTTP requests now use a 20-second timeout and retry up to five times to avoid API timeouts.
It can also run **TruffleHog** scans on repositories to leverage their advanced secret hunting heuristics.

It also includes a **Recon module** that discovers references to your company across third‑party services like Slack or Google Docs. These URLs are gathered from live queries and the Wayback Machine, then verified asynchronously so you know whether each link is still reachable.

This project was originally created by **محمد الحقباني** to help security researchers uncover leaks and protect their organizations. The goal is to build the strongest global tool of its kind. Please use it responsibly for legitimate security testing only.
In addition, a **Smart JS Scanner** can crawl JavaScript files from any domain (including optional subdomains and archived copies via the Wayback Machine).

When commit scanning is enabled, GitHub results also include leaked secrets found in commit messages and diffs, allowing detection of tokens in deleted files.
An optional **Deep Scan** mode searches GitHub issues in addition to code and commits for more thorough coverage. You can also enable **Full Repo Scan** to crawl every file in selected repositories or entire organizations, ensuring nothing is missed. A new **Wayback Repo** option downloads archived versions of repository files from the Wayback Machine so even deleted content is inspected. You can further enable **commit history** and **pull request** scanning so diffs and deleted files are inspected for secrets as well.
GitHub searches leverage a curated list of "dorks" sourced from the public [GitDorker](https://github.com/obheda12/GitDorker/) project. These prebuilt queries combine with your keyword to uncover common secret patterns across GitHub.

The tool ships with a list of over 200 regex patterns derived from the public database at [secrets.ninja](https://secrets.ninja/) and expanded with rules from [iwatchr.iscan.today](https://iwatchr.iscan.today/). These patterns cover a wide variety of API keys and tokens to improve detection accuracy. Additional generic patterns inspired by [Search for all leaked keys](https://github.com/Lu3ky13/Search-for-all-leaked-keys-secrets-using-one-regex-) help detect common password or API key assignments.
Recent updates also integrate private key signatures (RSA, DSA, EC and PGP) and JWT formats. All patterns are combined into a single master regex so scanning large files is much faster while still labeling each leak by type.
Additional patterns now detect Supabase, Vercel, Railway, Kaggle, Asana and Bugcrowd tokens for even broader coverage. Slack bot tokens, HuggingFace access tokens and Zendesk secrets are also included so leaks from those services are flagged.
New patterns also detect GitHub app secrets, GitHub Enterprise PATs, Telegram API credentials and ChatGPT API keys. We incorporated leak types highlighted on the **@arshadkazmi42** feed (creator of iScan.today) so tokens like *Mistral AI keys*, *Zoom JWTs* and *Discord webhooks* are recognized as well.

To further reduce false positives, matches are filtered using a small entropy check. Short or low‑entropy strings are ignored unless they resemble real credentials. Generic patterns also require at least one digit so ordinary words like `generator-app` aren't flagged.

It can optionally search employees automatically by inspecting the contributors of a repository you provide. You can also search an entire GitHub organization in one go by supplying an org name. A modern web interface on `localhost:8000` lets you run scans and view results. The UI is styled with Bootstrap for a clean look and now lets you toggle AI verification, commit scanning and silent mode directly from your browser. A dedicated `/scans` page lists all scans with their status.
The dashboard keeps a history of all scans and shows whether each one is still running or finished. You can open a **Live** view to watch results stream in as they are discovered, or view the final report once the scan is done.
Results appear on the page in real time thanks to server‑sent events, so you can monitor a scan while it is still running.
The web dashboard uses the dark **Darkly** theme for a sleek, modern look. Rows fade in as leaks appear for a smoother experience.
Full Auto Mode executes all searchers concurrently to accelerate large scans.
For quick checks you can enable the **Top Leaks** option, which searches GitHub for ten of the most commonly leaked API tokens such as AWS, Slack and HuggingFace keys.
Leak results may also be verified by a free AI classifier. When enabled from the prompts or the web form, each detected token is checked with a lightweight model from HuggingFace to reduce false positives. For even more accuracy you can enable *active verification*, which issues small HTTP requests (via `curl`) to confirm that URLs are reachable or that tokens remain valid by calling their APIs (GitHub, Slack, Discord, Telegram, etc.). Optional Telegram or Discord notifications can alert you when leaks are found. Verification runs asynchronously so scans remain fast, and the web UI includes a **Verified Only** filter to quickly review confirmed leaks.
The CLI now highlights the severity of each finding in color for quick triage.
When active verification is enabled, each leak is tested with a tiny HTTP request. Unverified results are discarded so the report only lists tokens that still work.
Public GitHub Gists are also scanned to catch secrets that might be shared outside repositories.
For deeper analysis you can enable the **TruffleHog** searcher, which runs the open source tool over selected repositories to analyze their full commit history.

## Usage

```
python3 emploleaks.py
```
Install the dependencies first:

```
pip install -r requirements.txt
```

At startup you will be asked for API tokens for GitHub, GitLab, SwaggerHub and GrayHatWarfare.
You can provide **multiple GitHub tokens** separated by commas to avoid rate limits—the
tool will rotate between them automatically. Providing tokens greatly improves results on
those platforms. If you skip a token or provide an invalid one, searches on that platform
may return no results and you may see warning messages. GitHub's code search API in
particular **requires** authentication. When no GitHub token is supplied the tool now warns
and skips GitHub results instead of timing out.

Follow the prompts to perform a normal scan on a chosen platform, run the Smart JS scan, or run full auto mode across all supported platforms. When employee scanning is enabled you will be asked for a repository name (owner/repo) and the tool will automatically gather contributor usernames. If you disable employee scanning you may still provide a repository path so only that repo is searched. Results now stream to the terminal immediately whenever a leak is found, and the same events are forwarded to the web UI if it is running. This lets you monitor progress in both places at once. After each scan an HTML report `results.html` **and** a machine-readable JSON file `results.json` are saved with the complete links and color-coded severity. You can also launch the web interface from the menu, which mirrors CLI scans automatically.

If you enable **Full Repo Scan**, the GitHub searcher crawls every file in each selected repository (or the entire organization) rather than relying solely on the search API. This thorough mode may take significantly longer. The **Wayback Repo** option can additionally fetch archived snapshots of those files to detect secrets that were deleted from history. Optional switches allow scanning commit history and pull requests too, and a **Top Leaks** mode queries GitHub for the most common API keywords like AWS, Slack, HuggingFace and Zendesk keys.

To use the web interface separately, run:

```
python3 webapp.py
```

While a scan runs, results stream live to the page using server‑sent events, so you can watch leaks appear in real time without waiting for the full scan to finish.

The refreshed dark interface (now using the **Darkly** Bootswatch theme) shows live results in color-coded tables with running counters for High, Medium, Low and Info leaks. Rows fade in smoothly and you can filter by platform, severity or keyword while the scan runs. The CLI also prints progress messages such as `Scanning owner/repo (3/10)` so you know which repository is being processed.

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
